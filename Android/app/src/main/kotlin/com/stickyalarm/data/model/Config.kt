package com.stickyalarm.data.model

import kotlinx.serialization.Serializable

@Serializable
data class Config(
    val scheduleProfiles: List<ScheduleProfile> = listOf(
        ScheduleProfile(id = "default", name = "Abends")
    ),
    val triggers: List<TriggerEntry> = listOf(
        TriggerEntry(name = "com.google.android.youtube", type = "app", profileId = "default"),
        TriggerEntry(name = "com.instagram.android", type = "app", profileId = "default"),
    ),
    val snoozeMinutes: Int = 15,
    val popupTitle: String = "Alarm",
    val popupText: String = "Dein System hat heute geliefert.\nJetzt darf es sich erholen.",
    val snoozeLabel: String = "Schlummern",
    val confirmLabel: String = "Abendroutine starten",
    val fullscreenPopup: Boolean = true,
    val vibrate: Boolean = true,
    val breakEnabled: Boolean = false,
    val breakIntervalMinutes: Int = 60,
    val breakDurationMinutes: Int = 5,
    val breakSnoozeMinutes: Int = 5,
    val breakPopupTitle: String = "Pause",
    val breakPopupText: String = "Steh auf, streck dich, trink Wasser.",
    val breakFullscreen: Boolean = false,
    val breakIcon: String = "\u2615",
    val autostartOnBoot: Boolean = false
) {
    val defaultProfile: ScheduleProfile get() = scheduleProfiles.first()

    fun getProfileForTrigger(trigger: TriggerEntry): ScheduleProfile {
        if (trigger.profileId.isNotEmpty()) {
            scheduleProfiles.find { it.id == trigger.profileId }?.let { return it }
        }
        return defaultProfile
    }

    fun getTriggersForProfile(profileId: String): List<TriggerEntry> {
        return triggers.filter {
            it.profileId == profileId || (it.profileId.isEmpty() && profileId == defaultProfile.id)
        }
    }

    fun getSnoozeForProfile(profile: ScheduleProfile): Int {
        return if (profile.snoozeMinutes > 0) profile.snoozeMinutes else snoozeMinutes
    }

    fun getTriggersInWindow(hour: Int, minute: Int): List<TriggerEntry> {
        return triggers.filter { trigger ->
            val profile = getProfileForTrigger(trigger)
            profile.schedule.isInWindow(hour, minute)
        }
    }

    fun anyProfileActive(hour: Int, minute: Int): Boolean {
        return scheduleProfiles.any { it.schedule.isInWindow(hour, minute) }
    }

    fun getActiveProfile(hour: Int, minute: Int): ScheduleProfile? {
        return scheduleProfiles.find { it.schedule.isInWindow(hour, minute) }
    }
}
