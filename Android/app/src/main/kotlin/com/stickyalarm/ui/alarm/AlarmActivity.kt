package com.stickyalarm.ui.alarm

import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.stickyalarm.service.AlarmForegroundService
import com.stickyalarm.service.NotificationHelper
import com.stickyalarm.ui.theme.StickyAlarmTheme
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat

class AlarmActivity : ComponentActivity() {

    private var vibrator: Vibrator? = null
    private var isBeingDismissed = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        isRunning = true

        // Show over lock screen
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        }
        window.addFlags(
            WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON or
            WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
            WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON
        )

        // Hide status bar and navigation bar for true fullscreen
        WindowCompat.setDecorFitsSystemWindows(window, false)
        WindowInsetsControllerCompat(window, window.decorView).let { controller ->
            controller.hide(WindowInsetsCompat.Type.statusBars() or WindowInsetsCompat.Type.navigationBars())
            controller.systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        }

        // Cancel the notification since the activity is now showing
        val nm = getSystemService(NotificationManager::class.java)
        nm.cancel(NotificationHelper.ALARM_NOTIFICATION_ID)

        val title = intent.getStringExtra(AlarmForegroundService.EXTRA_TITLE) ?: "Alarm"
        val text = intent.getStringExtra(AlarmForegroundService.EXTRA_TEXT) ?: ""
        val snoozeLabel = intent.getStringExtra(AlarmForegroundService.EXTRA_SNOOZE_LABEL) ?: "Schlummern"
        val confirmLabel = intent.getStringExtra(AlarmForegroundService.EXTRA_CONFIRM_LABEL) ?: "Abendroutine starten"
        val fullscreen = intent.getBooleanExtra(AlarmForegroundService.EXTRA_FULLSCREEN, true)
        val shouldVibrate = intent.getBooleanExtra(AlarmForegroundService.EXTRA_VIBRATE, true)

        if (shouldVibrate) {
            vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vm = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                vm.defaultVibrator
            } else {
                @Suppress("DEPRECATION")
                getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
            }
            val pattern = longArrayOf(0, 300, 200, 300, 200, 300)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator?.vibrate(VibrationEffect.createWaveform(pattern, -1))
            } else {
                @Suppress("DEPRECATION")
                vibrator?.vibrate(pattern, -1)
            }
        }

        setContent {
            StickyAlarmTheme {
                AlarmScreen(
                    title = title,
                    text = text,
                    snoozeLabel = snoozeLabel,
                    confirmLabel = confirmLabel,
                    fullscreen = fullscreen,
                    onSnooze = {
                        sendAction(AlarmForegroundService.ACTION_SNOOZE)
                        returnToPreviousApp()
                    },
                    onConfirm = {
                        sendAction(AlarmForegroundService.ACTION_CONFIRM)
                        returnToPreviousApp()
                    }
                )
            }
        }
    }

    private fun returnToPreviousApp() {
        isBeingDismissed = true
        isRunning = false
        finishAndRemoveTask()
    }

    private fun sendAction(action: String) {
        val intent = Intent(this, AlarmForegroundService::class.java).apply {
            this.action = action
        }
        startService(intent)
    }

    override fun onStop() {
        super.onStop()
        if (!isBeingDismissed && !isFinishing) {
            val relaunchIntent = Intent(this, AlarmActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                putExtras(intent)
            }
            startActivity(relaunchIntent)
        }
    }

    @Deprecated("Use onBackPressedDispatcher")
    override fun onBackPressed() {
        // Block back button during alarm
    }

    override fun onDestroy() {
        isRunning = false
        vibrator?.cancel()
        super.onDestroy()
    }

    companion object {
        @Volatile
        var isRunning = false
    }
}
