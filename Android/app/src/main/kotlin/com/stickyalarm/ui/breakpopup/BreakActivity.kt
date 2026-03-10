package com.stickyalarm.ui.breakpopup

import android.app.NotificationManager
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.stickyalarm.service.AlarmForegroundService
import com.stickyalarm.service.NotificationHelper
import com.stickyalarm.ui.theme.StickyAlarmTheme
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat

class BreakActivity : ComponentActivity() {

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
        nm.cancel(NotificationHelper.BREAK_NOTIFICATION_ID)

        val title = intent.getStringExtra(AlarmForegroundService.EXTRA_TITLE) ?: "Pause"
        val text = intent.getStringExtra(AlarmForegroundService.EXTRA_TEXT) ?: ""
        val fullscreen = intent.getBooleanExtra(AlarmForegroundService.EXTRA_FULLSCREEN, false)
        val durationMinutes = intent.getIntExtra(AlarmForegroundService.EXTRA_BREAK_DURATION, 5)
        val breakIcon = intent.getStringExtra(AlarmForegroundService.EXTRA_BREAK_ICON) ?: "☕"
        val breakSnooze = intent.getIntExtra(AlarmForegroundService.EXTRA_BREAK_SNOOZE, 5)

        setContent {
            StickyAlarmTheme {
                BreakScreen(
                    title = title,
                    text = text,
                    fullscreen = fullscreen,
                    durationMinutes = durationMinutes,
                    breakIcon = breakIcon,
                    breakSnoozeMinutes = breakSnooze,
                    onSnooze = {
                        sendAction(AlarmForegroundService.ACTION_BREAK_SNOOZE)
                        dismissBreak()
                    },
                    onDismiss = {
                        sendAction(AlarmForegroundService.ACTION_BREAK_SKIP)
                        dismissBreak()
                    }
                )
            }
        }
    }

    private fun dismissBreak() {
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
            val relaunchIntent = Intent(this, BreakActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                putExtras(intent)
            }
            startActivity(relaunchIntent)
        }
    }

    @Deprecated("Use onBackPressedDispatcher")
    override fun onBackPressed() {
        // Block back button during break — user must use snooze button
    }

    override fun onDestroy() {
        isRunning = false
        super.onDestroy()
    }

    companion object {
        @Volatile
        var isRunning = false
    }
}
