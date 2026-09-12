package com.example.evim.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

enum class EvimThemeMode(val title: String, val primaryColor: Color) {
    TURUNCU("Turuncu", Color(0xFFFF6F3C)),
    GECE_MAVISI("Gece Mavisi", Color(0xFF2C6BED)),
    ZUMRUT("Zümrüt", Color(0xFF2D9D6E)),
    OKYANUS("Okyanus", Color(0xFF0284C7)),
    YAKUT("Yakut", Color(0xFFC83E5D)),
    AMETIST("Ametist", Color(0xFF8E44AD)),
    MINIMAL("Minimal", Color(0xFF475569))
}

@Composable
fun EvimAppTheme(
    selectedTheme: EvimThemeMode = EvimThemeMode.TURUNCU,
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val primary = selectedTheme.primaryColor

    val colorScheme = if (darkTheme) {
        darkColorScheme(
            primary = primary,
            onPrimary = Color.White,
            primaryContainer = primary.copy(alpha = 0.25f),
            onPrimaryContainer = Color.White,
            secondary = primary.copy(alpha = 0.8f),
            onSecondary = Color.White,
            background = Color(0xFF121417),
            onBackground = Color(0xFFECEFF1),
            surface = Color(0xFF1E2228),
            onSurface = Color(0xFFECEFF1),
            surfaceVariant = Color(0xFF262C34),
            onSurfaceVariant = Color(0xFFB0BEC5),
            outline = Color(0xFF455A64)
        )
    } else {
        lightColorScheme(
            primary = primary,
            onPrimary = Color.White,
            primaryContainer = primary.copy(alpha = 0.12f),
            onPrimaryContainer = primary,
            secondary = primary.copy(alpha = 0.85f),
            onSecondary = Color.White,
            background = Color(0xFFF7F9FC),
            onBackground = Color(0xFF1A1C1E),
            surface = Color.White,
            onSurface = Color(0xFF1A1C1E),
            surfaceVariant = Color(0xFFEEF2F6),
            onSurfaceVariant = Color(0xFF5A626A),
            outline = Color(0xFFD6DCE2)
        )
    }

    MaterialTheme(
        colorScheme = colorScheme,
        content = content
    )
}
