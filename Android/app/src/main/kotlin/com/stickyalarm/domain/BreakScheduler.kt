package com.stickyalarm.domain

import com.stickyalarm.data.model.Config
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.temporal.ChronoUnit

enum class BreakState {
    IDLE, RUNNING, BREAK_DUE, BREAK_ACTIVE, SNOOZED
}

class BreakScheduler(private var config: Config) {
    var state: BreakState = BreakState.IDLE
        private set
    private var nextBreak: LocalDateTime? = null
    private var breakEnd: LocalDateTime? = null
    private var snoozeEnd: LocalDateTime? = null
    private var lastTickTime: Long = System.currentTimeMillis()
    private var pauseStartTime: LocalDateTime? = null

    init {
        if (config.breakEnabled) resetTimer()
    }

    private fun resetTimer() {
        nextBreak = LocalDateTime.now().plus(config.breakIntervalMinutes.toLong(), ChronoUnit.MINUTES)
        breakEnd = null
        snoozeEnd = null
        lastTickTime = System.currentTimeMillis()
        pauseStartTime = null
        state = BreakState.RUNNING
    }

    fun tick(): BreakState {
        if (!config.breakEnabled) {
            state = BreakState.IDLE
            return state
        }

        val now = LocalDateTime.now()

        when (state) {
            BreakState.IDLE -> resetTimer()
            BreakState.RUNNING -> {
                val nb = nextBreak
                if (nb != null && !now.isBefore(nb)) {
                    state = BreakState.BREAK_DUE
                }
            }
            BreakState.BREAK_ACTIVE -> {
                val be = breakEnd
                if (be != null && !now.isBefore(be)) {
                    resetTimer()
                }
            }
            BreakState.SNOOZED -> {
                val se = snoozeEnd
                if (se != null && !now.isBefore(se)) {
                    state = BreakState.BREAK_DUE
                }
            }
            BreakState.BREAK_DUE -> { /* wait for startBreak() call */ }
        }

        return state
    }

    fun startBreak() {
        state = BreakState.BREAK_ACTIVE
        breakEnd = LocalDateTime.now().plus(config.breakDurationMinutes.toLong(), ChronoUnit.MINUTES)
    }

    fun snooze() {
        state = BreakState.SNOOZED
        snoozeEnd = LocalDateTime.now().plus(config.breakSnoozeMinutes.toLong(), ChronoUnit.MINUTES)
    }

    fun skipBreak() {
        resetTimer()
    }

    fun remainingBreakSeconds(): Int {
        if (state == BreakState.BREAK_ACTIVE && breakEnd != null) {
            return maxOf(0, ChronoUnit.SECONDS.between(LocalDateTime.now(), breakEnd!!).toInt())
        }
        return 0
    }

    fun reset() {
        state = BreakState.IDLE
        nextBreak = null
        breakEnd = null
        snoozeEnd = null
        pauseStartTime = null
        lastTickTime = System.currentTimeMillis()
        if (config.breakEnabled) {
            state = BreakState.RUNNING
            nextBreak = LocalDateTime.now().plus(config.breakIntervalMinutes.toLong(), ChronoUnit.MINUTES)
        }
    }

    /** Pause timer — called when device is locked. Freezes all scheduled times. */
    fun pause() {
        if (pauseStartTime == null && state != BreakState.IDLE) {
            pauseStartTime = LocalDateTime.now()
        }
    }

    /** Resume timer — called when device is unlocked. Shifts scheduled times forward by pause duration. */
    fun resume() {
        val ps = pauseStartTime ?: return
        pauseStartTime = null
        val pausedSeconds = ChronoUnit.SECONDS.between(ps, LocalDateTime.now())
        if (pausedSeconds <= 0) return
        // Shift all scheduled times forward so timer doesn't fire during lock time
        nextBreak = nextBreak?.plus(pausedSeconds, ChronoUnit.SECONDS)
        breakEnd = breakEnd?.plus(pausedSeconds, ChronoUnit.SECONDS)
        snoozeEnd = snoozeEnd?.plus(pausedSeconds, ChronoUnit.SECONDS)
    }

    fun isPaused(): Boolean = pauseStartTime != null

    fun getRemainingSnoozeSeconds(): Int {
        if (state != BreakState.SNOOZED || snoozeEnd == null) return -1
        val remaining = ChronoUnit.SECONDS.between(LocalDateTime.now(), snoozeEnd!!)
        return if (remaining > 0) remaining.toInt() else 0
    }

    fun getSnoozeEndEpochMillis(): Long {
        if (snoozeEnd == null) return 0L
        return snoozeEnd!!.atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
    }

    fun getRemainingUntilBreak(): Int {
        if (state != BreakState.RUNNING || nextBreak == null) return -1
        val remaining = ChronoUnit.SECONDS.between(LocalDateTime.now(), nextBreak!!)
        return if (remaining > 0) remaining.toInt() else 0
    }

    fun reloadConfig(newConfig: Config) {
        val oldConfig = config
        config = newConfig
        if (!config.breakEnabled) {
            state = BreakState.IDLE
            nextBreak = null
            breakEnd = null
            snoozeEnd = null
        } else if (state == BreakState.IDLE) {
            resetTimer()
        } else if (oldConfig.breakIntervalMinutes != newConfig.breakIntervalMinutes && state == BreakState.RUNNING) {
            resetTimer()
        }
    }
}
