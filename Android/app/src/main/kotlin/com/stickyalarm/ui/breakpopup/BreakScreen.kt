package com.stickyalarm.ui.breakpopup

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.stickyalarm.ui.theme.*
import kotlinx.coroutines.delay

@Composable
fun BreakScreen(
    title: String,
    text: String,
    fullscreen: Boolean,
    durationMinutes: Int,
    breakIcon: String = "☕",
    breakSnoozeMinutes: Int = 5,
    onSnooze: () -> Unit,
    onDismiss: () -> Unit
) {
    var visible by remember { mutableStateOf(false) }
    val alpha by animateFloatAsState(
        targetValue = if (visible) 1f else 0f,
        animationSpec = tween(300),
        label = "fade"
    )
    LaunchedEffect(Unit) { visible = true }

    val totalSeconds = durationMinutes * 60
    var remainingSeconds by remember { mutableIntStateOf(totalSeconds) }
    val progress = remainingSeconds.toFloat() / totalSeconds.toFloat()

    // Countdown timer
    LaunchedEffect(Unit) {
        while (remainingSeconds > 0) {
            delay(1000)
            remainingSeconds--
        }
        onDismiss()
    }

    val minutes = remainingSeconds / 60
    val seconds = remainingSeconds % 60
    val timeDisplay = "%02d:%02d".format(minutes, seconds)

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(StickyBlack)
            .alpha(alpha),
        contentAlignment = Alignment.Center
    ) {
        Card(
            modifier = Modifier
                .widthIn(max = 400.dp)
                .padding(24.dp),
            shape = RoundedCornerShape(22.dp),
            colors = CardDefaults.cardColors(containerColor = StickyCard)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(32.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Coffee icon
                Text(
                    text = breakIcon,
                    fontSize = 44.sp
                )

                Spacer(modifier = Modifier.height(20.dp))

                // Title
                Text(
                    text = title,
                    style = MaterialTheme.typography.displayLarge,
                    color = StickyText,
                    textAlign = TextAlign.Center
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Subtitle
                Text(
                    text = text,
                    style = MaterialTheme.typography.bodyLarge,
                    color = StickyTextSecondary,
                    textAlign = TextAlign.Center
                )

                Spacer(modifier = Modifier.height(24.dp))

                // Countdown
                Text(
                    text = timeDisplay,
                    fontSize = 48.sp,
                    color = StickyText,
                    textAlign = TextAlign.Center,
                    letterSpacing = 4.sp
                )

                Spacer(modifier = Modifier.height(20.dp))

                // Progress bar
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(6.dp)
                        .clip(RoundedCornerShape(3.dp))
                        .background(StickyInput)
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxHeight()
                            .fillMaxWidth(fraction = progress)
                            .clip(RoundedCornerShape(3.dp))
                            .background(StickyAccent)
                    )
                }

                Spacer(modifier = Modifier.height(28.dp))

                // Snooze button
                OutlinedButton(
                    onClick = onSnooze,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = StickyTextSecondary
                    )
                ) {
                    Text(
                        text = "Schlummern ($breakSnoozeMinutes Min)",
                        style = MaterialTheme.typography.labelLarge
                    )
                }
            }
        }
    }
}
