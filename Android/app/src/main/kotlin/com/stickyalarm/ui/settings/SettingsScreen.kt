package com.stickyalarm.ui.settings

import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.stickyalarm.R
import com.stickyalarm.data.model.*
import com.stickyalarm.ui.theme.*
import com.stickyalarm.util.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    viewModel: SettingsViewModel = hiltViewModel(),
    onTestAlarm: () -> Unit = {}
) {
    val config by viewModel.config.collectAsState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var saveFlash by remember { mutableStateOf(false) }

    // Collapsible section states
    var alarmDisplayExpanded by remember { mutableStateOf(false) }
    var breakTimerExpanded by remember { mutableStateOf(false) }

    // Permission state
    var hasUsageStats by remember { mutableStateOf(hasUsageStatsPermission(context)) }
    var hasBattery by remember { mutableStateOf(isBatteryOptimizationIgnored(context)) }
    var hasNotifs by remember { mutableStateOf(hasNotificationPermission(context)) }
    var hasFullScreen by remember { mutableStateOf(hasFullScreenIntentPermission(context)) }
    var hasOverlay by remember { mutableStateOf(hasOverlayPermission(context)) }

    val notifLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted -> hasNotifs = granted }

    // Observe save success
    LaunchedEffect(Unit) {
        viewModel.saveSuccess.collect {
            saveFlash = true
            delay(800)
            saveFlash = false
        }
    }

    // Refresh permission state when resumed
    LaunchedEffect(Unit) {
        while (true) {
            delay(1000)
            hasUsageStats = hasUsageStatsPermission(context)
            hasBattery = isBatteryOptimizationIgnored(context)
            hasNotifs = hasNotificationPermission(context)
            hasFullScreen = hasFullScreenIntentPermission(context)
            hasOverlay = hasOverlayPermission(context)
        }
    }

    Scaffold(
        containerColor = StickyBlack,
        bottomBar = {
            Surface(
                color = StickyBlack,
                shadowElevation = 8.dp
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 12.dp)
                        .navigationBarsPadding(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    OutlinedButton(
                        onClick = onTestAlarm,
                        modifier = Modifier.weight(1f).height(52.dp),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = StickyTextSecondary)
                    ) {
                        Text(stringResource(R.string.alarm_testen))
                    }
                    Button(
                        onClick = { viewModel.save() },
                        modifier = Modifier.weight(1f).height(52.dp),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (saveFlash) StickySuccess else StickyAccent,
                            contentColor = StickyBlack
                        )
                    ) {
                        Text(
                            if (saveFlash) stringResource(R.string.gespeichert)
                            else stringResource(R.string.speichern),
                            style = MaterialTheme.typography.labelLarge
                        )
                    }
                }
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp)
                .statusBarsPadding()
        ) {
            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = stringResource(R.string.app_name),
                style = MaterialTheme.typography.headlineLarge,
                color = StickyText
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Permissions warning
            if (!hasUsageStats || !hasBattery || !hasNotifs || !hasFullScreen || !hasOverlay) {
                PermissionsSection(
                    hasUsageStats = hasUsageStats,
                    hasBattery = hasBattery,
                    hasNotifs = hasNotifs,
                    hasFullScreen = hasFullScreen,
                    hasOverlay = hasOverlay,
                    onGrantUsageStats = { openUsageStatsSettings(context) },
                    onGrantBattery = { requestIgnoreBatteryOptimization(context) },
                    onGrantNotifs = {
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            notifLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                        }
                    },
                    onGrantFullScreen = { openFullScreenIntentSettings(context) },
                    onGrantOverlay = { openOverlaySettings(context) }
                )
                Spacer(modifier = Modifier.height(24.dp))
            }

            // === ZEITPROFILE ===
            SectionHeader(stringResource(R.string.zeitprofile))
            Spacer(modifier = Modifier.height(12.dp))

            config.scheduleProfiles.forEach { profile ->
                ProfileCard(
                    profile = profile,
                    config = config,
                    triggers = config.getTriggersForProfile(profile.id),
                    canDelete = config.scheduleProfiles.size > 1,
                    onUpdate = { updated -> viewModel.updateProfile(profile.id) { updated } },
                    onDelete = { viewModel.removeProfile(profile.id) },
                    onAddTrigger = { pkg -> viewModel.addTrigger(profile.id, pkg) },
                    onRemoveTrigger = { name -> viewModel.removeTrigger(name, profile.id) },
                    onUpdateTriggerLimit = { name, min -> viewModel.updateTriggerTimeLimit(name, profile.id, min) }
                )
                Spacer(modifier = Modifier.height(12.dp))
            }

            OutlinedButton(
                onClick = { viewModel.addProfile() },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = StickyTextMuted)
            ) {
                Text(stringResource(R.string.neues_profil))
            }

            Spacer(modifier = Modifier.height(32.dp))

            // === ALARM-ANZEIGE (collapsible) ===
            CollapsibleSectionHeader(
                title = stringResource(R.string.alarm_anzeige),
                expanded = alarmDisplayExpanded,
                onToggle = { alarmDisplayExpanded = !alarmDisplayExpanded }
            )
            Spacer(modifier = Modifier.height(12.dp))
            AnimatedVisibility(visible = alarmDisplayExpanded) {
                SettingsCard {
                    SwitchRow(
                        label = stringResource(R.string.fullscreen_alarm),
                        checked = config.fullscreenPopup,
                        onCheckedChange = { viewModel.updateConfig { c -> c.copy(fullscreenPopup = it) } }
                    )
                    HorizontalDivider(color = StickySeparator)
                    SwitchRow(
                        label = stringResource(R.string.vibration),
                        checked = config.vibrate,
                        onCheckedChange = { viewModel.updateConfig { c -> c.copy(vibrate = it) } }
                    )
                    HorizontalDivider(color = StickySeparator)
                    SwitchRow(
                        label = stringResource(R.string.autostart_boot),
                        checked = config.autostartOnBoot,
                        onCheckedChange = { viewModel.updateConfig { c -> c.copy(autostartOnBoot = it) } }
                    )
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            // === PAUSENTIMER (collapsible) ===
            CollapsibleSectionHeader(
                title = stringResource(R.string.pausentimer),
                expanded = breakTimerExpanded,
                onToggle = { breakTimerExpanded = !breakTimerExpanded }
            )
            Spacer(modifier = Modifier.height(12.dp))
            AnimatedVisibility(visible = breakTimerExpanded) {
                BreakSection(
                    config = config,
                    onUpdate = { newConfig -> viewModel.updateConfig { newConfig } }
                )
            }

            Spacer(modifier = Modifier.height(100.dp))
        }
    }
}

@Composable
fun CollapsibleSectionHeader(
    title: String,
    expanded: Boolean,
    onToggle: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onToggle() }
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            color = StickyTextMuted
        )
        Icon(
            imageVector = if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
            contentDescription = null,
            tint = StickyTextMuted
        )
    }
}

@Composable
fun SectionHeader(title: String) {
    Text(
        text = title,
        style = MaterialTheme.typography.titleMedium,
        color = StickyTextMuted
    )
}

@Composable
fun SettingsCard(content: @Composable ColumnScope.() -> Unit) {
    Card(
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = StickyCard)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            content = content
        )
    }
}

@Composable
fun SwitchRow(
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyLarge,
            color = StickyText
        )
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            colors = SwitchDefaults.colors(
                checkedThumbColor = StickyAccent,
                checkedTrackColor = StickyBorderFocus,
                uncheckedThumbColor = StickyTextMuted,
                uncheckedTrackColor = StickyInput
            )
        )
    }
}

@Composable
fun PermissionsSection(
    hasUsageStats: Boolean,
    hasBattery: Boolean,
    hasNotifs: Boolean,
    hasFullScreen: Boolean,
    hasOverlay: Boolean = true,
    onGrantUsageStats: () -> Unit,
    onGrantBattery: () -> Unit,
    onGrantNotifs: () -> Unit,
    onGrantFullScreen: () -> Unit,
    onGrantOverlay: () -> Unit = {}
) {
    Card(
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = StickyDangerDim)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = stringResource(R.string.berechtigungen),
                style = MaterialTheme.typography.titleMedium,
                color = StickyDanger
            )
            Spacer(modifier = Modifier.height(12.dp))

            if (!hasNotifs) {
                PermissionRow(
                    label = stringResource(R.string.perm_notifications),
                    description = stringResource(R.string.perm_notifications_desc),
                    granted = false,
                    onGrant = onGrantNotifs
                )
            }
            if (!hasUsageStats) {
                PermissionRow(
                    label = stringResource(R.string.perm_usage_stats),
                    description = stringResource(R.string.perm_usage_stats_desc),
                    granted = false,
                    onGrant = onGrantUsageStats
                )
            }
            if (!hasBattery) {
                PermissionRow(
                    label = stringResource(R.string.perm_battery),
                    description = stringResource(R.string.perm_battery_desc),
                    granted = false,
                    onGrant = onGrantBattery
                )
            }
            if (!hasOverlay) {
                PermissionRow(
                    label = "Über anderen Apps anzeigen",
                    description = "Wichtigste Berechtigung für Fullscreen-Popups",
                    granted = false,
                    onGrant = onGrantOverlay
                )
            }
            if (!hasFullScreen) {
                PermissionRow(
                    label = "Fullscreen-Alarm",
                    description = "Erlaubt Alarm-Popups auf dem Sperrbildschirm",
                    granted = false,
                    onGrant = onGrantFullScreen
                )
            }
        }
    }
}

@Composable
fun PermissionRow(
    label: String,
    description: String,
    granted: Boolean,
    onGrant: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(text = label, style = MaterialTheme.typography.bodyLarge, color = StickyText)
            Text(text = description, style = MaterialTheme.typography.bodySmall, color = StickyTextMuted)
        }
        Spacer(modifier = Modifier.width(12.dp))
        if (granted) {
            Text(stringResource(R.string.erteilt), color = StickySuccess, style = MaterialTheme.typography.labelMedium)
        } else {
            FilledTonalButton(
                onClick = onGrant,
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.filledTonalButtonColors(
                    containerColor = StickyDanger.copy(alpha = 0.15f),
                    contentColor = StickyDanger
                )
            ) {
                Text(stringResource(R.string.erteilen), style = MaterialTheme.typography.labelMedium)
            }
        }
    }
}
