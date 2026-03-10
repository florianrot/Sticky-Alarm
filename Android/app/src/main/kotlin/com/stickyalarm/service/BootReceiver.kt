package com.stickyalarm.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat
import com.stickyalarm.data.CONFIG_KEY
import com.stickyalarm.data.dataStore
import com.stickyalarm.data.model.Config
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action in listOf(
                Intent.ACTION_BOOT_COMPLETED,
                "android.intent.action.QUICKBOOT_POWERON",
                "com.htc.intent.action.QUICKBOOT_POWERON"
            )) {
            val autostart = runBlocking {
                try {
                    context.dataStore.data.first()[CONFIG_KEY]?.let {
                        Json { ignoreUnknownKeys = true }.decodeFromString<Config>(it).autostartOnBoot
                    } ?: false
                } catch (_: Exception) { false }
            }
            if (autostart) {
                val serviceIntent = Intent(context, AlarmForegroundService::class.java)
                ContextCompat.startForegroundService(context, serviceIntent)
            }
        }
    }
}
