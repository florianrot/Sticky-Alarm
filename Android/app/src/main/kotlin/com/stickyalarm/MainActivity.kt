package com.stickyalarm

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.stickyalarm.service.AlarmForegroundService
import com.stickyalarm.ui.settings.SettingsScreen
import com.stickyalarm.ui.theme.StickyAlarmTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // Start foreground service
        val serviceIntent = Intent(this, AlarmForegroundService::class.java)
        startForegroundService(serviceIntent)

        setContent {
            StickyAlarmTheme {
                SettingsScreen(
                    onTestAlarm = {
                        AlarmForegroundService.testAlarm(this)
                    }
                )
            }
        }
    }
}
