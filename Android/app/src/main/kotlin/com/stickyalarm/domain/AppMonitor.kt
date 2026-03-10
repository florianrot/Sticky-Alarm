package com.stickyalarm.domain

import android.app.usage.UsageStatsManager
import android.content.Context
import com.stickyalarm.data.model.TriggerEntry
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AppMonitor @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val usageStatsManager: UsageStatsManager =
        context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager

    fun getForegroundApp(): String? {
        val end = System.currentTimeMillis()
        val start = end - 10_000 // last 10 seconds for reliability
        val stats = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_BEST, start, end
        )
        return stats?.maxByOrNull { it.lastTimeUsed }?.packageName
    }

    fun getActiveMatches(triggers: List<TriggerEntry>): List<String> {
        val foreground = getForegroundApp() ?: return emptyList()
        return triggers.filter { trigger ->
            foreground.equals(trigger.name, ignoreCase = true)
        }.map { it.name }
    }

    fun hasUsageStatsPermission(): Boolean {
        val end = System.currentTimeMillis()
        val start = end - 60_000
        val stats = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_BEST, start, end
        )
        return stats != null && stats.isNotEmpty()
    }
}
