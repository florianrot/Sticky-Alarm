package com.stickyalarm.ui.theme

import android.app.Activity
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val StickyColorScheme = darkColorScheme(
    background = StickyBlack,
    surface = StickyCard,
    surfaceVariant = StickyInput,
    surfaceContainerHigh = StickyHover,
    onBackground = StickyText,
    onSurface = StickyText,
    onSurfaceVariant = StickyTextSecondary,
    primary = StickyAccent,
    onPrimary = StickyBlack,
    secondary = StickyTextSecondary,
    onSecondary = StickyBlack,
    error = StickyDanger,
    onError = StickyText,
    outline = StickyBorder,
    outlineVariant = StickyBorderFocus,
)

@Composable
fun StickyAlarmTheme(content: @Composable () -> Unit) {
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
            WindowCompat.getInsetsController(window, view).isAppearanceLightNavigationBars = false
        }
    }

    MaterialTheme(
        colorScheme = StickyColorScheme,
        typography = StickyTypography,
        content = content
    )
}
