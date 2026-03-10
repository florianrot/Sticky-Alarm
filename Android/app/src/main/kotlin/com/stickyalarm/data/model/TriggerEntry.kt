package com.stickyalarm.data.model

import kotlinx.serialization.Serializable

@Serializable
data class TriggerEntry(
    val name: String = "",
    val type: String = "app",
    val profileId: String = "",
    val timeLimitMinutes: Int = 0
) {
    val isTimeBased: Boolean get() = timeLimitMinutes > 0
}
