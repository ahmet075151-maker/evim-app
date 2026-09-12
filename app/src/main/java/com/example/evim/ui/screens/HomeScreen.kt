package com.example.evim.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.evim.data.model.EvimConstants
import com.example.evim.data.model.ItemEntity
import com.example.evim.data.model.RoomEntity
import com.example.evim.ui.components.AddEditRoomDialog
import com.example.evim.ui.components.ConfirmDeleteDialog
import com.example.evim.ui.components.EvimTopBar
import com.example.evim.ui.components.ItemDetailDialog
import com.example.evim.ui.components.RoomCard
import com.example.evim.ui.components.ThemeDialog
import com.example.evim.ui.viewmodel.EvimViewModel
import kotlinx.coroutines.launch

@Composable
fun HomeScreen(
    viewModel: EvimViewModel,
    onNavigateToRoom: (RoomEntity) -> Unit,
    onNavigateToSpecial: (type: String, title: String) -> Unit,
    onNavigateToHistory: () -> Unit
) {
    val rooms by viewModel.rooms.collectAsState()
    val allItems by viewModel.allItems.collectAsState()
    val totalCount by viewModel.totalCount.collectAsState()
    val totalValue by viewModel.totalValue.collectAsState()
    val lowStockItems by viewModel.lowStockItems.collectAsState()
    val isGuestMode by viewModel.isGuestMode.collectAsState()
    val currentTheme by viewModel.currentTheme.collectAsState()
    val searchQuery by viewModel.searchQuery.collectAsState()
    val searchResults by viewModel.searchResults.collectAsState()

    var showAddRoomDialog by remember { mutableStateOf(false) }
    var roomToEdit by remember { mutableStateOf<RoomEntity?>(null) }
    var roomToDelete by remember { mutableStateOf<RoomEntity?>(null) }
    var showThemeDialog by remember { mutableStateOf(false) }

    var selectedSearchItem by remember { mutableStateOf<ItemEntity?>(null) }
    var searchItemPath by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()

    Scaffold(
        topBar = {
            EvimTopBar(
                title = "Evim",
                canNavigateBack = false,
                onNavigateBack = {},
                isGuestMode = isGuestMode,
                onToggleGuestMode = { viewModel.toggleGuestMode() },
                onOpenThemeDialog = { showThemeDialog = true },
                onOpenFavorites = { onNavigateToSpecial("favorites", "Sık Kullanılanlar") },
                onOpenShoppingList = { onNavigateToSpecial("shopping", "Alışveriş / Eksik Listesi") },
                onOpenForSale = { onNavigateToSpecial("for_sale", "Satılık / Bağış Listesi") },
                onOpenLost = { onNavigateToSpecial("lost", "Kayıp Eşyalar") },
                onOpenMovingMode = { onNavigateToSpecial("moving", "Taşınma Modu") },
                onOpenRecent = { onNavigateToSpecial("recent", "Son Eklenenler") },
                onOpenHistory = onNavigateToHistory,
                onExportCsv = { viewModel.copyExportData(viewModel.getApplication()) }
            )
        },
        floatingActionButton = {
            if (!isGuestMode && searchQuery.isBlank()) {
                FloatingActionButton(
                    onClick = { showAddRoomDialog = true },
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = Color.White,
                    modifier = Modifier.testTag("add_room_fab")
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Default.Add, contentDescription = "Oda Ekle")
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Oda Ekle", fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            // Search field
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { viewModel.setSearchQuery(it) },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp)
                    .testTag("home_search_input"),
                placeholder = { Text("Tüm eşyalarda veya etiketlerde ara...") },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                trailingIcon = {
                    if (searchQuery.isNotBlank()) {
                        IconButton(onClick = { viewModel.setSearchQuery("") }) {
                            Icon(Icons.Default.Clear, contentDescription = "Temizle")
                        }
                    }
                },
                singleLine = true,
                shape = RoundedCornerShape(14.dp)
            )

            if (searchQuery.isNotBlank()) {
                // Search Results list
                Text(
                    text = "${searchResults.size} sonuç bulundu:",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)
                )
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(searchResults, key = { it.id }) { item ->
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable {
                                    scope.launch {
                                        searchItemPath = viewModel.repository.buildFullBreadcrumb(item)
                                        selectedSearchItem = item
                                    }
                                },
                            shape = RoundedCornerShape(12.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(10.dp)
                                        .clip(CircleShape)
                                        .background(EvimConstants.getCategoryColor(item.category))
                                )
                                Spacer(modifier = Modifier.width(10.dp))
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        text = item.name,
                                        fontWeight = FontWeight.SemiBold,
                                        fontSize = 15.sp
                                    )
                                    val room = rooms.find { it.id == item.roomId }
                                    Text(
                                        text = "${room?.name ?: "Oda"} • ${item.category} • ${item.qty} ${item.unit}",
                                        fontSize = 12.sp,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                                if (item.price > 0) {
                                    Text(
                                        text = "${item.price.toInt()} ₺",
                                        fontWeight = FontWeight.Bold,
                                        color = MaterialTheme.colorScheme.primary,
                                        fontSize = 14.sp
                                    )
                                }
                            }
                        }
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // Summary metrics
                    item {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Card(
                                modifier = Modifier.weight(1f),
                                shape = RoundedCornerShape(16.dp),
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f)
                                )
                            ) {
                                Column(modifier = Modifier.padding(14.dp)) {
                                    Text("Toplam Eşya", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text("$totalCount", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                                }
                            }

                            Card(
                                modifier = Modifier.weight(1f),
                                shape = RoundedCornerShape(16.dp),
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.6f)
                                )
                            ) {
                                Column(modifier = Modifier.padding(14.dp)) {
                                    Text("Toplam Değer", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text("${totalValue.toInt()} ₺", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }

                    // Low stock alert banner
                    if (lowStockItems.isNotEmpty()) {
                        item {
                            Card(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable { onNavigateToSpecial("shopping", "Alışveriş / Eksik Listesi") },
                                shape = RoundedCornerShape(14.dp),
                                colors = CardDefaults.cardColors(
                                    containerColor = Color(0xFFFFEBEE)
                                )
                            ) {
                                Row(
                                    modifier = Modifier.padding(14.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.ShoppingCart,
                                        contentDescription = null,
                                        tint = Color(0xFFC62828)
                                    )
                                    Spacer(modifier = Modifier.width(12.dp))
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(
                                            text = "Stoğu Azalan ${lowStockItems.size} Eşya Var",
                                            fontWeight = FontWeight.Bold,
                                            color = Color(0xFFC62828),
                                            fontSize = 14.sp
                                        )
                                        Text(
                                            text = "Alışveriş listesini görüntülemek için dokunun",
                                            fontSize = 12.sp,
                                            color = Color(0xFFB71C1C)
                                        )
                                    }
                                }
                            }
                        }
                    }

                    // Categories horizontal row
                    item {
                        Column {
                            Text(
                                text = "Kategoriler",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            LazyRow(
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                items(EvimConstants.ITEM_CATEGORIES) { cat ->
                                    val catColor = EvimConstants.getCategoryColor(cat)
                                    val count = allItems.count { it.category == cat }
                                    Box(
                                        modifier = Modifier
                                            .clip(RoundedCornerShape(12.dp))
                                            .background(catColor.copy(alpha = 0.12f))
                                            .clickable {
                                                onNavigateToSpecial("category:$cat", "Kategori: $cat")
                                            }
                                            .padding(horizontal = 14.dp, vertical = 8.dp)
                                    ) {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            Box(
                                                modifier = Modifier
                                                    .size(8.dp)
                                                    .clip(CircleShape)
                                                    .background(catColor)
                                            )
                                            Spacer(modifier = Modifier.width(6.dp))
                                            Text(
                                                text = "$cat ($count)",
                                                fontSize = 13.sp,
                                                fontWeight = FontWeight.Medium,
                                                color = catColor
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Rooms section
                    item {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Odalar (${rooms.size})",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }

                    if (rooms.isEmpty()) {
                        item {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 32.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = "Henüz oda eklenmemiş.\n'Oda Ekle' butonuna dokunarak başlayın.",
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    fontSize = 14.sp
                                )
                            }
                        }
                    } else {
                        items(rooms, key = { it.id }) { room ->
                            val count = allItems.count { it.roomId == room.id }
                            RoomCard(
                                room = room,
                                itemCount = count,
                                isGuestMode = isGuestMode,
                                onClick = { onNavigateToRoom(room) },
                                onEdit = { roomToEdit = room },
                                onDelete = { roomToDelete = room }
                            )
                        }
                    }

                    item {
                        Spacer(modifier = Modifier.height(72.dp))
                    }
                }
            }
        }
    }

    // Dialogs
    if (showAddRoomDialog) {
        AddEditRoomDialog(
            onDismiss = { showAddRoomDialog = false },
            onSave = { name, type ->
                viewModel.addRoom(name, type)
                showAddRoomDialog = false
            }
        )
    }

    if (roomToEdit != null) {
        AddEditRoomDialog(
            initialRoom = roomToEdit,
            onDismiss = { roomToEdit = null },
            onSave = { name, type ->
                viewModel.updateRoom(roomToEdit!!.copy(name = name, roomType = type))
                roomToEdit = null
            }
        )
    }

    if (roomToDelete != null) {
        ConfirmDeleteDialog(
            title = "Odayı Sil",
            message = "'${roomToDelete!!.name}' odası ve içindeki tüm eşyalar silinecektir. Silinenler geçmişinden geri getirebilirsiniz.",
            onDismiss = { roomToDelete = null },
            onConfirm = {
                viewModel.deleteRoom(roomToDelete!!)
                roomToDelete = null
            }
        )
    }

    if (showThemeDialog) {
        ThemeDialog(
            currentTheme = currentTheme,
            onDismiss = { showThemeDialog = false },
            onSelect = {
                viewModel.setTheme(it)
                showThemeDialog = false
            }
        )
    }

    if (selectedSearchItem != null) {
        ItemDetailDialog(
            item = selectedSearchItem!!,
            breadcrumbPath = searchItemPath,
            onDismiss = { selectedSearchItem = null },
            onEdit = {
                // Navigate or handle
                selectedSearchItem = null
            }
        )
    }
}
