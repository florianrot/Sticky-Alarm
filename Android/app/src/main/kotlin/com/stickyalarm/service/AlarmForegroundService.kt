package com.stickyalarm.service

import android.app.AlarmManager
import android.app.KeyguardManager
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.PixelFormat
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager
import android.os.SystemClock
import android.provider.Settings
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import com.stickyalarm.MainActivity
import com.stickyalarm.data.ConfigRepository
import com.stickyalarm.data.model.Config
import com.stickyalarm.data.model.ScheduleProfile
import com.stickyalarm.domain.*
import com.stickyalarm.ui.alarm.AlarmActivity
import com.stickyalarm.ui.breakpopup.BreakActivity
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import javax.inject.Inject

@AndroidEntryPoint
class AlarmForegroundService : Service() {

    @Inject lateinit var configRepository: ConfigRepository
    @Inject lateinit var appMonitor: AppMonitor

    private val handler = Handler(Looper.getMainLooper())
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())

    private lateinit var alarmScheduler: AlarmScheduler
    private lateinit var breakScheduler: BreakScheduler
    private lateinit var foregroundTracker: ForegroundTracker

    private var config = Config()
    private var alarmShowing = false
    private var breakShowing = false
    private var activeAlarmProfile: ScheduleProfile? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private var screenOffTime: Long = 0L

    private val screenReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            when (intent?.action) {
                Intent.ACTION_SCREEN_OFF -> {
                    screenOffTime = SystemClock.elapsedRealtime()
                }
                Intent.ACTION_SCREEN_ON -> {
                    if (screenOffTime > 0) {
                        val elapsed = SystemClock.elapsedRealtime() - screenOffTime
                        if (elapsed > 5 * 60 * 1000 && ::breakScheduler.isInitialized) {
                            breakScheduler.reset()
                        }
                        screenOffTime = 0L
                    }
                }
            }
        }
    }

    private val alarmTickReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == ACTION_ALARM_TICK) {
                tick()
                handler.removeCallbacks(tickRunnable)
                handler.postDelayed(tickRunnable, 5000)
                scheduleAlarmTick()
            }
        }
    }

    private val tickRunnable = object : Runnable {
        override fun run() {
            tick()
            handler.postDelayed(this, 5000)
        }
    }

    override fun onCreate() {
        super.onCreate()
        NotificationHelper.createChannels(this)

        foregroundTracker = ForegroundTracker()

        val filter = IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_OFF)
            addAction(Intent.ACTION_SCREEN_ON)
        }
        registerReceiver(screenReceiver, filter)

        val tickFilter = IntentFilter(ACTION_ALARM_TICK)
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(alarmTickReceiver, tickFilter, RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(alarmTickReceiver, tickFilter)
        }

        scope.launch {
            config = configRepository.load()
            alarmScheduler = AlarmScheduler(config)
            breakScheduler = BreakScheduler(config)

            startForeground(
                NotificationHelper.SERVICE_NOTIFICATION_ID,
                NotificationHelper.buildServiceNotification(this@AlarmForegroundService, getString(com.stickyalarm.R.string.service_notification_waiting))
            )

            handler.post(tickRunnable)
            scheduleAlarmTick()

            configRepository.configFlow.collect { newConfig ->
                config = newConfig
                if (::alarmScheduler.isInitialized) alarmScheduler.updateConfig(newConfig)
                if (::breakScheduler.isInitialized) breakScheduler.reloadConfig(newConfig)
            }
        }

        val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "StickyAlarm::TickWakeLock").apply {
            acquire()
        }
    }

    private fun scheduleAlarmTick() {
        val am = getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val intent = Intent(ACTION_ALARM_TICK).setPackage(packageName)
        val pi = PendingIntent.getBroadcast(
            this, 99, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S && !am.canScheduleExactAlarms()) {
            am.setAndAllowWhileIdle(
                AlarmManager.ELAPSED_REALTIME_WAKEUP,
                SystemClock.elapsedRealtime() + 60_000,
                pi
            )
        } else {
            am.setExactAndAllowWhileIdle(
                AlarmManager.ELAPSED_REALTIME_WAKEUP,
                SystemClock.elapsedRealtime() + 60_000,
                pi
            )
        }
    }

    private fun cancelAlarmTick() {
        val am = getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val intent = Intent(ACTION_ALARM_TICK).setPackage(packageName)
        val pi = PendingIntent.getBroadcast(
            this, 99, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        am.cancel(pi)
    }

    /** Check if device is unlocked and screen is on */
    private fun isDeviceUnlocked(): Boolean {
        val km = getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
        val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
        return pm.isInteractive && !km.isKeyguardLocked
    }

    /**
     * Launch an activity reliably from background using the overlay window trick.
     * Adds a temporary TYPE_APPLICATION_OVERLAY window to satisfy Android's
     * BAL "visible window" condition, then starts the activity.
     */
    private fun launchActivityFromBackground(intent: Intent) {
        if (Settings.canDrawOverlays(this)) {
            val wm = getSystemService(Context.WINDOW_SERVICE) as WindowManager
            val overlayView = View(this)
            val params = WindowManager.LayoutParams(
                0, 0,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE,
                PixelFormat.TRANSLUCENT
            )
            params.gravity = Gravity.TOP or Gravity.START
            var viewAdded = false
            try {
                wm.addView(overlayView, params)
                viewAdded = true
            } catch (_: Exception) {}

            try {
                startActivity(intent)
            } catch (_: Exception) {}

            if (viewAdded) {
                handler.postDelayed({
                    try { wm.removeView(overlayView) } catch (_: Exception) {}
                }, 500)
            }
        } else {
            try {
                startActivity(intent)
            } catch (_: Exception) {}
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_SNOOZE -> {
                if (::alarmScheduler.isInitialized) {
                    val snoozeMin = if (activeAlarmProfile != null) config.getSnoozeForProfile(activeAlarmProfile!!) else config.snoozeMinutes
                    alarmScheduler.snooze(snoozeMin)
                    alarmShowing = false
                    foregroundTracker.resetAll()
                    val nm = getSystemService(NotificationManager::class.java)
                    nm.cancel(NotificationHelper.ALARM_NOTIFICATION_ID)
                }
            }
            ACTION_CONFIRM -> {
                if (::alarmScheduler.isInitialized) {
                    alarmScheduler.confirmRoutine()
                    alarmShowing = false
                    foregroundTracker.resetAll()
                    activeAlarmProfile = null
                    val nm = getSystemService(NotificationManager::class.java)
                    nm.cancel(NotificationHelper.ALARM_NOTIFICATION_ID)
                }
            }
            ACTION_BREAK_SNOOZE -> {
                if (::breakScheduler.isInitialized) {
                    breakScheduler.snooze()
                    breakShowing = false
                    showBreakSnoozedNotification()
                }
            }
            ACTION_BREAK_SKIP -> {
                if (::breakScheduler.isInitialized) {
                    breakScheduler.skipBreak()
                    breakShowing = false
                    val nm = getSystemService(NotificationManager::class.java)
                    nm.cancel(NotificationHelper.BREAK_NOTIFICATION_ID)
                }
            }
            ACTION_TEST_ALARM -> {
                if (::alarmScheduler.isInitialized) {
                    alarmScheduler.forceTrigger()
                }
            }
        }
        return START_STICKY
    }

    private fun tick() {
        if (!::alarmScheduler.isInitialized) return

        val unlocked = isDeviceUnlocked()
        val alarmState = alarmScheduler.tick()

        // === BREAK timer: pause when locked, resume when unlocked ===
        if (::breakScheduler.isInitialized) {
            if (!unlocked) {
                breakScheduler.pause()
            } else {
                breakScheduler.resume()
            }
        }

        // Only tick break scheduler when unlocked (timer is frozen when locked)
        val breakState = if (unlocked && ::breakScheduler.isInitialized) {
            breakScheduler.tick()
        } else if (::breakScheduler.isInitialized) {
            breakScheduler.state
        } else {
            BreakState.IDLE
        }

        // === BREAK has priority — process first (only when unlocked) ===
        when (breakState) {
            BreakState.BREAK_DUE -> {
                if (!breakShowing && unlocked) {
                    if (alarmShowing) {
                        alarmShowing = false
                        val nm = getSystemService(NotificationManager::class.java)
                        nm.cancel(NotificationHelper.ALARM_NOTIFICATION_ID)
                    }
                    breakScheduler.startBreak()
                    showBreak()
                    breakShowing = true
                }
            }
            BreakState.BREAK_ACTIVE -> {
                // Activity re-launch handled by onStop() in BreakActivity
            }
            BreakState.SNOOZED -> {
                // Notification already posted by ACTION_BREAK_SNOOZE handler
            }
            else -> {
                if ((breakState == BreakState.IDLE || breakState == BreakState.RUNNING) && breakShowing) {
                    breakShowing = false
                    val nm = getSystemService(NotificationManager::class.java)
                    nm.cancel(NotificationHelper.BREAK_NOTIFICATION_ID)
                }
            }
        }

        // === ALARM — queued behind break ===
        when (alarmState) {
            AlarmState.ACTIVE -> {
                if (!alarmShowing && !breakShowing) {
                    showAlarm()
                    alarmShowing = true
                }
            }
            AlarmState.CONFIRMED -> {
                if (alarmShowing) alarmShowing = false
                checkTriggers()
            }
            AlarmState.WAITING -> {
                if (alarmShowing) alarmShowing = false
                foregroundTracker.resetAll()
            }
            AlarmState.SNOOZED -> {
                if (alarmShowing) alarmShowing = false
            }
        }

        if (::breakScheduler.isInitialized && config.breakEnabled) {
            _breakRemainingSeconds.value = breakScheduler.getRemainingUntilBreak()
        } else {
            _breakRemainingSeconds.value = -1
        }

        updateNotification(alarmState)
    }

    private fun checkTriggers() {
        val now = LocalDateTime.now()
        val activeTriggers = config.getTriggersInWindow(now.hour, now.minute)
        if (activeTriggers.isEmpty()) return

        val matches = appMonitor.getActiveMatches(activeTriggers)
        foregroundTracker.updateActiveMatches(matches)

        for (trigger in activeTriggers) {
            if (trigger.isTimeBased) {
                if (trigger.name in matches && foregroundTracker.hasExceededLimit(trigger)) {
                    foregroundTracker.resetAll()
                    alarmScheduler.triggerDetected()
                    break
                }
            } else {
                if (trigger.name in matches) {
                    alarmScheduler.triggerDetected()
                    break
                }
            }
        }
    }

    private fun showAlarm() {
        val now = LocalDateTime.now()
        val profile = config.getActiveProfile(now.hour, now.minute)
        activeAlarmProfile = profile

        val title = profile?.alarmTitle?.ifEmpty { null } ?: config.popupTitle
        val text = profile?.alarmMessage?.ifEmpty { null } ?: config.popupText
        val snoozeLabel = profile?.snoozeLabel?.ifEmpty { null } ?: config.snoozeLabel
        val confirmLabel = profile?.confirmLabel?.ifEmpty { null } ?: config.confirmLabel

        val intent = Intent(this, AlarmActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            putExtra(EXTRA_TITLE, title)
            putExtra(EXTRA_TEXT, text)
            putExtra(EXTRA_SNOOZE_LABEL, snoozeLabel)
            putExtra(EXTRA_CONFIRM_LABEL, confirmLabel)
            putExtra(EXTRA_FULLSCREEN, config.fullscreenPopup)
            putExtra(EXTRA_VIBRATE, config.vibrate)
        }

        val snoozePendingIntent = PendingIntent.getService(
            this, 20,
            Intent(this, AlarmForegroundService::class.java).apply { action = ACTION_SNOOZE },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val fullScreenPendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationHelper.buildAlarmNotification(
            this, title, fullScreenPendingIntent, snoozePendingIntent
        )
        val nm = getSystemService(NotificationManager::class.java)
        nm.cancel(NotificationHelper.ALARM_NOTIFICATION_ID)
        nm.notify(NotificationHelper.ALARM_NOTIFICATION_ID, notification)

        launchActivityFromBackground(intent)
    }

    private fun showBreak() {
        if (config.breakFullscreen) {
            val intent = Intent(this, BreakActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                putExtra(EXTRA_TITLE, config.breakPopupTitle)
                putExtra(EXTRA_TEXT, config.breakPopupText)
                putExtra(EXTRA_FULLSCREEN, true)
                putExtra(EXTRA_BREAK_DURATION, config.breakDurationMinutes)
                putExtra(EXTRA_BREAK_ICON, config.breakIcon)
                putExtra(EXTRA_BREAK_SNOOZE, config.breakSnoozeMinutes)
            }

            val fullScreenPendingIntent = PendingIntent.getActivity(
                this, 1, intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )

            val snoozePendingIntent = PendingIntent.getService(
                this, 10,
                Intent(this, AlarmForegroundService::class.java).apply { action = ACTION_BREAK_SNOOZE },
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )

            val notification = NotificationHelper.buildBreakNotification(
                this, config.breakPopupTitle, config.breakPopupText,
                fullScreenPendingIntent, snoozePendingIntent
            )
            val nm = getSystemService(NotificationManager::class.java)
            nm.cancel(NotificationHelper.BREAK_NOTIFICATION_ID)
            nm.notify(NotificationHelper.BREAK_NOTIFICATION_ID, notification)

            launchActivityFromBackground(intent)
        } else {
            val snoozePendingIntent = PendingIntent.getService(
                this, 10,
                Intent(this, AlarmForegroundService::class.java).apply { action = ACTION_BREAK_SNOOZE },
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            val skipPendingIntent = PendingIntent.getService(
                this, 11,
                Intent(this, AlarmForegroundService::class.java).apply { action = ACTION_BREAK_SKIP },
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )

            val notification = NotificationHelper.buildBreakNotificationOnly(
                this, config.breakPopupTitle, config.breakPopupText,
                config.breakDurationMinutes, snoozePendingIntent, skipPendingIntent
            )
            val nm = getSystemService(NotificationManager::class.java)
            nm.cancel(NotificationHelper.BREAK_NOTIFICATION_ID)
            nm.notify(NotificationHelper.BREAK_NOTIFICATION_ID, notification)
        }
    }

    private fun showBreakSnoozedNotification() {
        val snoozeEndMillis = breakScheduler.getSnoozeEndEpochMillis()
        if (snoozeEndMillis <= 0L) return
        val tapIntent = PendingIntent.getActivity(
            this, 1,
            Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val notification = NotificationHelper.buildBreakSnoozedNotification(
            this, snoozeEndMillis, tapIntent
        )
        val nm = getSystemService(NotificationManager::class.java)
        nm.notify(NotificationHelper.BREAK_NOTIFICATION_ID, notification)
    }

    private fun updateNotification(state: AlarmState) {
        val text = when (state) {
            AlarmState.WAITING -> getString(com.stickyalarm.R.string.service_notification_waiting)
            AlarmState.ACTIVE -> "Alarm aktiv"
            AlarmState.SNOOZED -> {
                val formatter = DateTimeFormatter.ofPattern("HH:mm")
                val until = LocalDateTime.now().plusMinutes(config.snoozeMinutes.toLong())
                getString(com.stickyalarm.R.string.service_notification_snoozed, until.format(formatter))
            }
            AlarmState.CONFIRMED -> getString(com.stickyalarm.R.string.service_notification_confirmed)
        }

        val nm = getSystemService(NotificationManager::class.java)
        nm.notify(
            NotificationHelper.SERVICE_NOTIFICATION_ID,
            NotificationHelper.buildServiceNotification(this, text)
        )
    }

    override fun onTaskRemoved(rootIntent: Intent?) {
        super.onTaskRemoved(rootIntent)
        val restartIntent = Intent(this, AlarmForegroundService::class.java)
        startForegroundService(restartIntent)
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        handler.removeCallbacks(tickRunnable)
        cancelAlarmTick()
        try { unregisterReceiver(screenReceiver) } catch (_: Exception) {}
        try { unregisterReceiver(alarmTickReceiver) } catch (_: Exception) {}
        scope.cancel()
        wakeLock?.release()
        super.onDestroy()
    }

    companion object {
        const val ACTION_SNOOZE = "com.stickyalarm.SNOOZE"
        const val ACTION_CONFIRM = "com.stickyalarm.CONFIRM"
        const val ACTION_BREAK_SNOOZE = "com.stickyalarm.BREAK_SNOOZE"
        const val ACTION_BREAK_SKIP = "com.stickyalarm.BREAK_SKIP"
        const val ACTION_TEST_ALARM = "com.stickyalarm.TEST_ALARM"
        const val ACTION_ALARM_TICK = "com.stickyalarm.ALARM_TICK"

        const val EXTRA_TITLE = "title"
        const val EXTRA_TEXT = "text"
        const val EXTRA_SNOOZE_LABEL = "snooze_label"
        const val EXTRA_CONFIRM_LABEL = "confirm_label"
        const val EXTRA_FULLSCREEN = "fullscreen"
        const val EXTRA_VIBRATE = "vibrate"
        const val EXTRA_BREAK_DURATION = "break_duration"
        const val EXTRA_BREAK_ICON = "break_icon"
        const val EXTRA_BREAK_SNOOZE = "break_snooze"

        private val _breakRemainingSeconds = MutableStateFlow(-1)
        val breakRemainingSeconds = _breakRemainingSeconds.asStateFlow()

        fun testAlarm(context: Context) {
            val intent = Intent(context, AlarmForegroundService::class.java).apply {
                action = ACTION_TEST_ALARM
            }
            context.startService(intent)
        }
    }
}
