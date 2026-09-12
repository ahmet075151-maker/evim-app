package com.example.evim.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EvimTopBar(
    title: String,
    canNavigateBack: Boolean,
    onNavigateBack: () -> Unit,
    isGuestMode: Boolean,
    onToggleGuestMode: () -> Unit,
    onOpenThemeDialog: () -> Unit,
    onOpenFavorites: () -> Unit,
    onOpenShoppingList: () -> Unit,
    onOpenForSale: () -> Unit,
    onOpenLost: () -> Unit,
    onOpenMovingMode: () -> Unit,
    onOpenRecent: () -> Unit,
    onOpenHistory: () -> Unit,
    onExportCsv: () -> Unit,
    modifier: Modifier = Modifier
) {
    var menuExpanded by remember { mutableStateOf(false) }

    TopAppBar(
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = title,
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp
                )
                if (isGuestMode) {
                    Spacer(modifier = Modifier.width(8.dp))
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(6.dp))
                            .background(Color(0xFFE65100).copy(alpha = 0.2f))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "Misafir Modu",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = Color(0xFFE65100)
                        )
                    }
                }
            }
        },
        navigationIcon = {
            if (canNavigateBack) {
                IconButton(
                    onClick = onNavigateBack,
                    modifier = Modifier.testTag("top_bar_back_button")
                ) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "Geri"
                    )
                }
            }
        },
        actions = {
            IconButton(
                onClick = onOpenThemeDialog,
                modifier = Modifier.testTag("theme_button")
            ) {
                Text("🎨", fontSize = 18.sp)
            }

            Box {
                IconButton(
                    onClick = { menuExpanded = true },
                    modifier = Modifier.testTag("top_bar_menu_button")
                ) {
                    Icon(
                        imageVector = Icons.Default.MoreVert,
                        contentDescription = "Ana Menü"
                    )
                }

                DropdownMenu(
                    expanded = menuExpanded,
                    onDismissRequest = { menuExpanded = false }
                ) {
                    DropdownMenuItem(
                        text = { Text("⭐ Sık Kullanılanlar") },
                        onClick = {
                            menuExpanded = false
                            onOpenFavorites()
                        }
                    )
                    DropdownMenuItem(
                        text = { Text("🛒 Alışveriş / Eksik Listesi") },
                        onClick = {
                            menuExpanded = false
                            onOpenShoppingList()
                        }
                    )
                    DropdownMenuItem(
                        text = { Text("🏷️ Satılık / Bağış") },
                        onClick = {
                            menuExpanded = false
                            onOpenForSale()
                        }
                    )
                    DropdownMenuItem(
                        text = { Text("❓ Kayıp Eşyalar") },
                        onClick = {
                            menuExpanded = false
                            onOpenLost()
                        }
                    )
                    DropdownMenuItem(
                        text = { Text("📦 Taşınma Modu (Koli No)") },
                        onClick = {
                            menuExpanded = false
                            onOpenMovingMode()
                        }
                    )
                    DropdownMenuItem(
                        text = { Text("🕒 Son Eklenenler") },
                        onClick = {
                            menuExpanded = false
                            onOpenRecent()
                        }
                    )
                    DropdownMenuItem(
                        text = { Text("🗑️ Silinenler Geçmişi") },
                        onClick = {
                            menuExpanded = false
                            onOpenHistory()
                        }
                    )
                    DropdownMenuItem(
                        text = { Text("📄 Dışa Aktar (CSV Kopyala)") },
                        onClick = {
                            menuExpanded = false
                            onExportCsv()
                        }
                    )
                    DropdownMenuItem(
                        text = {
                            Text(if (isGuestMode) "👁️ Misafir Modunu Kapat" else "👁️ Misafir Modunu Aç")
                        },
                        onClick = {
                            menuExpanded = false
                            onToggleGuestMode()
                        }
                    )
                    DropdownMenuItem(
                        text = { Text("🎨 Tema Değiştir") },
                        onClick = {
                            menuExpanded = false
                            onOpenThemeDialog()
                        }
                    )
                }
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = MaterialTheme.colorScheme.surface,
            titleContentColor = MaterialTheme.colorScheme.onSurface,
            navigationIconContentColor = MaterialTheme.colorScheme.onSurface,
            actionIconContentColor = MaterialTheme.colorScheme.onSurface
        ),
        modifier = modifier
    )
}
