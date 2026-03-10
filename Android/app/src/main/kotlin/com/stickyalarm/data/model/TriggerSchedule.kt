package com.stickyalarm.data.model

import kotlinx.serialization.Serializable

@Serializable
data class TriggerSchedule(
    val startHour: Int = 20,
    val startMinute: Int = 0,
    val endHour: Int = 4,
    val endMinute: Int = 0
) {
    fun isInWindow(hour: Int, minute: Int): Boolean {
        val start = startHour * 60 + startMinute
        val end = endHour * 60 + endMinute
        val now = hour * 60 + minute
        return if (start <= end) now in start until end
        else now >= start || now < end
    }

    val display: String
        get() = "${startHour.toString().padStart(2, '0')}:${startMinute.toString().padStart(2, '0')} - ${endHour.toString().padStart(2, '0')}:${endMinute.toString().padStart(2, '0')}"
}
