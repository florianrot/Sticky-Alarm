package com.stickyalarm.ui.settings

import android.app.TimePickerDialog
import androidx.compose.animation.*
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.stickyalarm.R
import com.stickyalarm.data.model.*
import com.stickyalarm.ui.theme.*
import androidx.compose.foundation.Image
import androidx.compose.ui.graphics.asImageBitmap
import androidx.core.graphics.drawable.toBitmap
import com.stickyalarm.util.*

@Composable
fun ProfileCard(
    profile: ScheduleProfile,
    config: Config,
    triggers: List<TriggerEntry>,
    canDelete: Boolean,
    onUpdate: (ScheduleProfile) -> Unit,
    onDelete: () -> Unit,
    onAddTrigger: (String) -> Unit,
    onRemoveTrigger: (String) -> Unit,
    onUpdateTriggerLimit: (String, Int) -> Unit
) {
    var expanded by remember { mutableStateOf(false) }
    var showDeleteDialog by remember { mutableStateOf(false) }
    var showAppPicker by remember { mutableStateOf(false) }
    val context = LocalContext.current

    // Build exclude set for app picker
    val triggerPackages = remember(triggers) { triggers.map { it.name }.toSet() }

    if (showDeleteDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            title = { Text(stringResource(R.string.profil_loeschen)) },
            text = { Text(stringResource(R.string.profil_loeschen_bestaetigen)) },
            confirmButton = {
                TextButton(onClick = { showDeleteDialog = false; onDelete() }) {
                    Text(stringResource(R.string.loeschen), color = StickyDanger)
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteDialog = false }) {
                    Text(stringResource(R.string.abbrechen))
                }
            },
            containerColor = StickyCard
        )
    }

    if (showAppPicker) {
        AppPickerDialog(
            excludePackages = triggerPackages,
            onSelect = { pkg -> showAppPicker = false; onAddTrigger(pkg) },
            onDismiss = { showAppPicker = false }
        )
    }

    Card(
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = StickyCard)
    ) {
        Column {
            // Header (clickable to expand/collapse)
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { expanded = !expanded }
                    .padding(16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = profile.name.ifEmpty { "Profil" },
                        style = MaterialTheme.typography.titleLarge,
                        color = StickyText
                    )
                    Text(
                        text = profile.schedule.display,
                        style = MaterialTheme.typography.bodySmall,
                        color = StickyTextMuted
                    )
                }
                Row {
                    if (canDelete) {
                        IconButton(onClick = { showDeleteDialog = true }) {
                            Icon(Icons.Default.Delete, contentDescription = null, tint = StickyDanger)
                        }
                    }
                    Icon(
                        imageVector = if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                        contentDescription = null,
                        tint = StickyTextMuted
                    )
                }
            }

            // Expandable content
            AnimatedVisibility(visible = expanded) {
                Column(modifier = Modifier.padding(start = 16.dp, end = 16.dp, bottom = 16.dp)) {
                    HorizontalDivider(color = StickySeparator)
                    Spacer(modifier = Modifier.height(12.dp))

                    // Name
                    OutlinedTextField(
                        value = profile.name,
                        onValueChange = { onUpdate(profile.copy(name = it)) },
                        label = { Text(stringResource(R.string.name)) },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        colors = stickyTextFieldColors()
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    // Time window
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        TimePickerButton(
                            label = stringResource(R.string.von),
                            hour = profile.schedule.startHour,
                            minute = profile.schedule.startMinute,
                            onTimeSet = { h, m ->
                                onUpdate(profile.copy(schedule = profile.schedule.copy(startHour = h, startMinute = m)))
                            },
                            modifier = Modifier.weight(1f)
                        )
                        TimePickerButton(
                            label = stringResource(R.string.bis),
                            hour = profile.schedule.endHour,
                            minute = profile.schedule.endMinute,
                            onTimeSet = { h, m ->
                                onUpdate(profile.copy(schedule = profile.schedule.copy(endHour = h, endMinute = m)))
                            },
                            modifier = Modifier.weight(1f)
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Snooze interval
                    NumberInputRow(
                        label = "${stringResource(R.string.schlummer_intervall)} (${stringResource(R.string.minuten)})",
                        value = profile.snoozeMinutes,
                        onValueChange = { onUpdate(profile.copy(snoozeMinutes = it)) },
                        min = 1,
                        max = 120
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    // App Triggers (collapsible)
                    var showTriggers by remember { mutableStateOf(true) }
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { showTriggers = !showTriggers }
                            .padding(vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = stringResource(R.string.app_trigger),
                            style = MaterialTheme.typography.labelLarge,
                            color = StickyLabel
                        )
                        Icon(
                            if (showTriggers) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                            contentDescription = null,
                            tint = StickyTextMuted
                        )
                    }
                    AnimatedVisibility(visible = showTriggers) {
                        Column {
                            if (triggers.isEmpty()) {
                                Text(
                                    text = stringResource(R.string.keine_apps_konfiguriert),
                                    style = MaterialTheme.typography.bodySmall,
                                    color = StickyTextMuted
                                )
                            } else {
                                triggers.forEach { trigger ->
                                    TriggerRow(
                                        trigger = trigger,
                                        onRemove = { onRemoveTrigger(trigger.name) },
                                        onUpdateTimeLimit = { min -> onUpdateTriggerLimit(trigger.name, min) }
                                    )
                                }
                            }
                            Spacer(modifier = Modifier.height(8.dp))
                            OutlinedButton(
                                onClick = { showAppPicker = true },
                                shape = RoundedCornerShape(10.dp),
                                colors = ButtonDefaults.outlinedButtonColors(contentColor = StickyTextMuted)
                            ) {
                                Text(stringResource(R.string.hinzufuegen))
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Alarm text overrides (collapsible, collapsed by default)
                    var showTexts by remember { mutableStateOf(false) }
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { showTexts = !showTexts }
                            .padding(vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = stringResource(R.string.alarm_texte),
                            style = MaterialTheme.typography.labelLarge,
                            color = StickyLabel
                        )
                        Icon(
                            if (showTexts) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                            contentDescription = null,
                            tint = StickyTextMuted
                        )
                    }
                    AnimatedVisibility(visible = showTexts) {
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedTextField(
                                value = profile.alarmTitle,
                                onValueChange = { onUpdate(profile.copy(alarmTitle = it)) },
                                label = { Text(stringResource(R.string.alarm_titel_optional)) },
                                placeholder = { Text(config.popupTitle, color = StickyTextMuted) },
                                modifier = Modifier.fillMaxWidth(),
                                singleLine = true,
                                colors = stickyTextFieldColors()
                            )
                            OutlinedTextField(
                                value = profile.alarmMessage,
                                onValueChange = { onUpdate(profile.copy(alarmMessage = it)) },
                                label = { Text(stringResource(R.string.alarm_nachricht_optional)) },
                                placeholder = { Text(config.popupText, color = StickyTextMuted) },
                                modifier = Modifier.fillMaxWidth(),
                                minLines = 2,
                                colors = stickyTextFieldColors()
                            )
                            OutlinedTextField(
                                value = profile.snoozeLabel,
                                onValueChange = { onUpdate(profile.copy(snoozeLabel = it)) },
                                label = { Text(stringResource(R.string.schlummern_button_optional)) },
                                placeholder = { Text(config.snoozeLabel, color = StickyTextMuted) },
                                modifier = Modifier.fillMaxWidth(),
                                singleLine = true,
                                colors = stickyTextFieldColors()
                            )
                            OutlinedTextField(
                                value = profile.confirmLabel,
                                onValueChange = { onUpdate(profile.copy(confirmLabel = it)) },
                                label = { Text(stringResource(R.string.bestaetigen_button_optional)) },
                                placeholder = { Text(config.confirmLabel, color = StickyTextMuted) },
                                modifier = Modifier.fillMaxWidth(),
                                singleLine = true,
                                colors = stickyTextFieldColors()
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun TriggerRow(
    trigger: TriggerEntry,
    onRemove: () -> Unit,
    onUpdateTimeLimit: (Int) -> Unit
) {
    val context = LocalContext.current
    var textValue by remember(trigger.timeLimitMinutes) {
        mutableStateOf(if (trigger.timeLimitMinutes > 0) trigger.timeLimitMinutes.toString() else "")
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        val icon = remember(trigger.name) { getAppIcon(context, trigger.name) }
        if (icon != null) {
            val bitmap = remember(trigger.name) {
                icon.toBitmap(48, 48).asImageBitmap()
            }
            Image(
                bitmap = bitmap,
                contentDescription = null,
                modifier = Modifier.size(24.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
        }
        Text(
            text = getAppLabel(context, trigger.name),
            style = MaterialTheme.typography.bodyLarge,
            color = StickyText,
            modifier = Modifier.weight(1f)
        )
        // Time limit input
        OutlinedTextField(
            value = textValue,
            onValueChange = { newText ->
                val filtered = newText.filter { it.isDigit() }
                textValue = filtered
                val num = filtered.toIntOrNull()
                if (num != null) {
                    onUpdateTimeLimit(num.coerceIn(0, 999))
                }
            },
            placeholder = { Text("Min", style = MaterialTheme.typography.bodySmall) },
            modifier = Modifier
                .width(64.dp)
                .onFocusChanged { focusState ->
                    if (!focusState.isFocused) {
                        val num = textValue.toIntOrNull()
                        if (num == null || num <= 0) {
                            textValue = ""
                            onUpdateTimeLimit(0)
                        } else {
                            val clamped = num.coerceIn(1, 999)
                            textValue = clamped.toString()
                            onUpdateTimeLimit(clamped)
                        }
                    }
                },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            textStyle = MaterialTheme.typography.bodySmall,
            colors = stickyTextFieldColors()
        )
        IconButton(onClick = onRemove) {
            Icon(Icons.Default.Close, contentDescription = null, tint = StickyDanger, modifier = Modifier.size(18.dp))
        }
    }
}

@Composable
fun TimePickerButton(
    label: String,
    hour: Int,
    minute: Int,
    onTimeSet: (Int, Int) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    OutlinedButton(
        onClick = {
            TimePickerDialog(context, { _, h, m -> onTimeSet(h, m) }, hour, minute, true).show()
        },
        modifier = modifier.height(52.dp),
        shape = RoundedCornerShape(10.dp),
        colors = ButtonDefaults.outlinedButtonColors(contentColor = StickyText)
    ) {
        Text("$label: ${"%02d:%02d".format(hour, minute)}")
    }
}

@Composable
fun stickyTextFieldColors() = OutlinedTextFieldDefaults.colors(
    focusedBorderColor = StickyBorderFocus,
    unfocusedBorderColor = StickyBorder,
    focusedTextColor = StickyText,
    unfocusedTextColor = StickyText,
    cursorColor = StickyAccent,
    focusedLabelColor = StickyTextSecondary,
    unfocusedLabelColor = StickyTextMuted,
    focusedContainerColor = StickyInput,
    unfocusedContainerColor = StickyInput
)
