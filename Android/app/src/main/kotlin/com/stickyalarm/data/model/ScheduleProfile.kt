package com.stickyalarm.data.model

import kotlinx.serialization.Serializable

@Serializable
data class ScheduleProfile(
    val id: String = generateId(),
    val name: String = "Abends",
    val schedule: TriggerSchedule = TriggerSchedule(),
    val snoozeMinutes: Int = 15,
    val alarmTitle: String = "",
    val alarmMessage: String = "",
    val snoozeLabel: String = "",
    val confirmLabel: String = "",
    val launchApps: List<String> = emptyList()
)

fun generateId(): String = "${System.currentTimeMillis()}_${(0..9999).random()}"
