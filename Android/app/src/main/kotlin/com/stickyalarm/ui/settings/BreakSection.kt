package com.stickyalarm.ui.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.stickyalarm.data.model.Config
import com.stickyalarm.service.AlarmForegroundService
import com.stickyalarm.ui.theme.*
import kotlinx.coroutines.delay

@Composable
fun BreakSection(
    config: Config,
    onUpdate: (Config) -> Unit
) {
    val remainingSeconds by AlarmForegroundService.breakRemainingSeconds.collectAsState()
    var displaySeconds by remember { mutableIntStateOf(remainingSeconds) }

    // Sync from service
    LaunchedEffect(remainingSeconds) { displaySeconds = remainingSeconds }

    // Smooth local countdown
    LaunchedEffect(displaySeconds) {
        if (displaySeconds > 0) {
            delay(1000L)
            displaySeconds--
        }
    }

    Card(
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = StickyCard)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Enable toggle
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Pausentimer aktivieren",
                    style = MaterialTheme.typography.bodyLarge,
                    color = StickyText
                )
                Switch(
                    checked = config.breakEnabled,
                    onCheckedChange = {
                        onUpdate(config.copy(breakEnabled = it))
                    },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = StickyAccent,
                        checkedTrackColor = StickyBorderFocus,
                        uncheckedThumbColor = StickyTextMuted,
                        uncheckedTrackColor = StickyInput
                    )
                )
            }

            if (config.breakEnabled) {
                // Countdown display
                if (displaySeconds > 0) {
                    Spacer(modifier = Modifier.height(12.dp))
                    val min = displaySeconds / 60
                    val sec = displaySeconds % 60
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = "N\u00e4chste Pause in %02d:%02d".format(min, sec),
                            style = MaterialTheme.typography.bodyMedium,
                            color = StickyTextSecondary
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
                HorizontalDivider(color = StickySeparator)
                Spacer(modifier = Modifier.height(16.dp))

                // Interval
                NumberInputRow(
                    label = "Intervall (Minuten)",
                    value = config.breakIntervalMinutes,
                    onValueChange = { onUpdate(config.copy(breakIntervalMinutes = it.coerceIn(1, 240))) },
                    min = 1,
                    max = 240
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Duration
                NumberInputRow(
                    label = "Pausendauer (Minuten)",
                    value = config.breakDurationMinutes,
                    onValueChange = { onUpdate(config.copy(breakDurationMinutes = it.coerceIn(1, 30))) },
                    min = 1,
                    max = 30
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Snooze
                NumberInputRow(
                    label = "Schlummern (Minuten)",
                    value = config.breakSnoozeMinutes,
                    onValueChange = { onUpdate(config.copy(breakSnoozeMinutes = it.coerceIn(1, 30))) },
                    min = 1,
                    max = 30
                )

                Spacer(modifier = Modifier.height(16.dp))
                HorizontalDivider(color = StickySeparator)
                Spacer(modifier = Modifier.height(16.dp))

                // Display mode: Notification vs Fullscreen
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Anzeige",
                        style = MaterialTheme.typography.bodyLarge,
                        color = StickyText
                    )
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        FilterChip(
                            selected = !config.breakFullscreen,
                            onClick = { onUpdate(config.copy(breakFullscreen = false)) },
                            label = { Text("Benachrichtigung", style = MaterialTheme.typography.labelSmall) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = StickyAccent.copy(alpha = 0.15f),
                                selectedLabelColor = StickyAccent,
                                containerColor = StickyInput,
                                labelColor = StickyTextMuted
                            ),
                            shape = RoundedCornerShape(8.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        FilterChip(
                            selected = config.breakFullscreen,
                            onClick = { onUpdate(config.copy(breakFullscreen = true)) },
                            label = { Text("Fullscreen", style = MaterialTheme.typography.labelSmall) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = StickyAccent.copy(alpha = 0.15f),
                                selectedLabelColor = StickyAccent,
                                containerColor = StickyInput,
                                labelColor = StickyTextMuted
                            ),
                            shape = RoundedCornerShape(8.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
                HorizontalDivider(color = StickySeparator)
                Spacer(modifier = Modifier.height(16.dp))

                // Title
                Text("Titel", style = MaterialTheme.typography.labelMedium, color = StickyTextMuted)
                Spacer(modifier = Modifier.height(4.dp))
                OutlinedTextField(
                    value = config.breakPopupTitle,
                    onValueChange = { onUpdate(config.copy(breakPopupTitle = it)) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    colors = stickyTextFieldColors(),
                    shape = RoundedCornerShape(10.dp)
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Message
                Text("Nachricht", style = MaterialTheme.typography.labelMedium, color = StickyTextMuted)
                Spacer(modifier = Modifier.height(4.dp))
                OutlinedTextField(
                    value = config.breakPopupText,
                    onValueChange = { onUpdate(config.copy(breakPopupText = it)) },
                    minLines = 2,
                    modifier = Modifier.fillMaxWidth(),
                    colors = stickyTextFieldColors(),
                    shape = RoundedCornerShape(10.dp)
                )

                Spacer(modifier = Modifier.height(12.dp))

                // Icon
                Text("Icon", style = MaterialTheme.typography.labelMedium, color = StickyTextMuted)
                Spacer(modifier = Modifier.height(4.dp))
                OutlinedTextField(
                    value = config.breakIcon,
                    onValueChange = { onUpdate(config.copy(breakIcon = it)) },
                    singleLine = true,
                    modifier = Modifier.width(80.dp),
                    colors = stickyTextFieldColors(),
                    shape = RoundedCornerShape(10.dp)
                )
            }
        }
    }
}

@Composable
fun NumberInputRow(
    label: String,
    value: Int,
    onValueChange: (Int) -> Unit,
    min: Int = 0,
    max: Int = 999
) {
    var textValue by remember(value) { mutableStateOf(value.toString()) }
    var hasFocus by remember { mutableStateOf(false) }

    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyLarge,
            color = StickyText,
            modifier = Modifier.weight(1f)
        )
        OutlinedTextField(
            value = textValue,
            onValueChange = { newText ->
                val filtered = newText.filter { it.isDigit() }
                textValue = filtered
                val num = filtered.toIntOrNull()
                if (num != null) {
                    onValueChange(num.coerceIn(min, max))
                }
            },
            singleLine = true,
            modifier = Modifier
                .width(80.dp)
                .onFocusChanged { focusState ->
                    hasFocus = focusState.isFocused
                    if (!focusState.isFocused) {
                        val num = textValue.toIntOrNull()
                        if (num == null) {
                            textValue = min.toString()
                            onValueChange(min)
                        } else {
                            val clamped = num.coerceIn(min, max)
                            textValue = clamped.toString()
                            onValueChange(clamped)
                        }
                    }
                },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            colors = stickyTextFieldColors(),
            shape = RoundedCornerShape(10.dp)
        )
    }
}
