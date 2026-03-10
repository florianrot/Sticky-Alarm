package com.stickyalarm.domain

import com.stickyalarm.data.model.Config
import java.time.LocalDateTime
import java.time.temporal.ChronoUnit

enum class AlarmState {
    WAITING, ACTIVE, SNOOZED, CONFIRMED
}

class AlarmScheduler(private var config: Config) {
    var state: AlarmState = AlarmState.WAITING
        private set
    private var snoozeAfter: LocalDateTime? = null
    private var wasInWindow: Boolean = isInWindow()

    private fun isInWindow(): Boolean {
        val now = LocalDateTime.now()
        return config.anyProfileActive(now.hour, now.minute)
    }

    fun tick(): AlarmState {
        val now = LocalDateTime.now()
        val inWindow = config.anyProfileActive(now.hour, now.minute)

        if (!inWindow) {
            state = AlarmState.WAITING
            snoozeAfter = null
            wasInWindow = false
            return state
        }

        when (state) {
            AlarmState.WAITING -> {
                state = if (wasInWindow) {
                    wasInWindow = false
                    AlarmState.CONFIRMED
                } else {
                    AlarmState.ACTIVE
                }
            }
            AlarmState.SNOOZED -> {
                val after = snoozeAfter
                if (after != null && !now.isBefore(after)) {
                    state = AlarmState.ACTIVE
                    snoozeAfter = null
                }
            }
            AlarmState.ACTIVE, AlarmState.CONFIRMED -> { /* no-op, wait for user action or trigger */ }
        }

        return state
    }

    fun snooze(snoozeMinutes: Int? = null) {
        state = AlarmState.SNOOZED
        val minutes = snoozeMinutes ?: config.snoozeMinutes
        snoozeAfter = LocalDateTime.now().plus(minutes.toLong(), ChronoUnit.MINUTES)
    }

    fun confirmRoutine() {
        state = AlarmState.CONFIRMED
    }

    fun triggerDetected() {
        if (state == AlarmState.CONFIRMED) {
            state = AlarmState.ACTIVE
        }
    }

    fun forceTrigger() {
        state = AlarmState.ACTIVE
    }

    fun updateConfig(newConfig: Config) {
        config = newConfig
    }
}
