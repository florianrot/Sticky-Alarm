package com.stickyalarm.domain

import com.stickyalarm.data.model.TriggerEntry

class ForegroundTracker {
    private val active = mutableMapOf<String, Double>()
    private val lastUpdate = mutableMapOf<String, Double>()
    private val lastSeen = mutableMapOf<String, Long>()

    companion object {
        private const val COOLDOWN_MS = 5 * 60 * 1000L // 5 min cooldown
    }

    fun updateActiveMatches(matchedNames: List<String>) {
        val now = System.currentTimeMillis() / 1000.0
        val nowMs = System.currentTimeMillis()
        val current = matchedNames.toSet()

        for (name in current) {
            val last = lastUpdate[name]
            if (last != null) {
                val delta = now - last
                if (delta < 15) {
                    active[name] = (active[name] ?: 0.0) + delta
                }
            }
            lastUpdate[name] = now
            lastSeen[name] = nowMs
        }

        // Inactive triggers: check cooldown
        for (name in active.keys.toList()) {
            if (name !in current) {
                lastUpdate.remove(name)
                val ls = lastSeen[name] ?: 0L
                if (nowMs - ls >= COOLDOWN_MS) {
                    // 5 min inactive -> reset counter
                    active.remove(name)
                    lastSeen.remove(name)
                }
                // Otherwise: counter stays (no reset on brief pause)
            }
        }
    }

    fun hasExceededLimit(trigger: TriggerEntry): Boolean {
        if (!trigger.isTimeBased) return false
        val accumulated = active[trigger.name] ?: 0.0
        return accumulated >= trigger.timeLimitMinutes * 60
    }

    fun resetTrigger(name: String) {
        active.remove(name)
        lastUpdate.remove(name)
        lastSeen.remove(name)
    }

    fun resetAll() {
        active.clear()
        lastUpdate.clear()
        lastSeen.clear()
    }
}
