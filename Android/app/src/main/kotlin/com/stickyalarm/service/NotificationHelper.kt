package com.stickyalarm.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import com.stickyalarm.MainActivity
import com.stickyalarm.R

object NotificationHelper {

    const val SERVICE_CHANNEL_ID = "sticky_alarm_service"
    const val ALARM_CHANNEL_ID = "sticky_alarm_alarm"
    const val BREAK_CHANNEL_ID = "sticky_alarm_break"

    const val SERVICE_NOTIFICATION_ID = 1
    const val ALARM_NOTIFICATION_ID = 2
    const val BREAK_NOTIFICATION_ID = 3

    fun createChannels(context: Context) {
        val nm = context.getSystemService(NotificationManager::class.java)

        val serviceChannel = NotificationChannel(
            SERVICE_CHANNEL_ID,
            context.getString(R.string.notification_channel_service),
            NotificationManager.IMPORTANCE_MIN
        ).apply {
            description = context.getString(R.string.notification_channel_service_desc)
            setShowBadge(false)
            setSound(null, null)
        }

        val alarmChannel = NotificationChannel(
            ALARM_CHANNEL_ID,
            context.getString(R.string.notification_channel_alarm),
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = context.getString(R.string.notification_channel_alarm_desc)
            setBypassDnd(true)
            setSound(null, null)
            enableVibration(false)
            lockscreenVisibility = Notification.VISIBILITY_PUBLIC
        }

        val breakChannel = NotificationChannel(
            BREAK_CHANNEL_ID,
            context.getString(R.string.notification_channel_break),
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = context.getString(R.string.notification_channel_break_desc)
            setSound(null, null)
            enableVibration(true)
            lockscreenVisibility = Notification.VISIBILITY_PUBLIC
        }

        nm.createNotificationChannels(listOf(serviceChannel, alarmChannel, breakChannel))
    }

    fun buildServiceNotification(context: Context, text: String): Notification {
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            context, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(context, SERVICE_CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentText(text)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setSilent(true)
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_DEFERRED)
            .build()
    }

    fun buildAlarmNotification(
        context: Context,
        title: String,
        fullScreenIntent: PendingIntent,
        snoozePendingIntent: PendingIntent
    ): Notification {
        return NotificationCompat.Builder(context, ALARM_CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(context.getString(R.string.alarm_notification_text))
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setFullScreenIntent(fullScreenIntent, true)
            .setContentIntent(fullScreenIntent)
            .setAutoCancel(false)
            .setOngoing(true)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .addAction(0, "Schlummern", snoozePendingIntent)
            .build()
    }

    fun buildBreakNotification(
        context: Context,
        title: String,
        text: String,
        fullScreenIntent: PendingIntent,
        snoozePendingIntent: PendingIntent
    ): Notification {
        return NotificationCompat.Builder(context, BREAK_CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(text)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setFullScreenIntent(fullScreenIntent, true)
            .setContentIntent(fullScreenIntent)
            .setAutoCancel(false)
            .setOngoing(true)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .addAction(0, "Schlummern", snoozePendingIntent)
            .build()
    }

    fun buildBreakSnoozedNotification(
        context: Context,
        snoozeEndMillis: Long,
        tapIntent: PendingIntent
    ): Notification {
        return NotificationCompat.Builder(context, BREAK_CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("Pause geschlummert")
            .setContentText("Nächste Pause in...")
            .setWhen(snoozeEndMillis)
            .setUsesChronometer(true)
            .setChronometerCountDown(true)
            .setShowWhen(true)
            .setOngoing(true)
            .setAutoCancel(false)
            .setSilent(true)
            .setContentIntent(tapIntent)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .build()
    }

    fun buildBreakNotificationOnly(
        context: Context,
        title: String,
        text: String,
        durationMinutes: Int,
        snoozePendingIntent: PendingIntent,
        skipPendingIntent: PendingIntent
    ): Notification {
        return NotificationCompat.Builder(context, BREAK_CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(text)
            .setSubText("${durationMinutes} Min. Pause")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setAutoCancel(false)
            .setOngoing(true)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .addAction(0, "Schlummern", snoozePendingIntent)
            .addAction(0, "\u00dcberspringen", skipPendingIntent)
            .build()
    }
}
