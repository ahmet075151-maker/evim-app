package com.example.evim.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
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
import com.example.evim.data.model.ItemEntity
import com.example.evim.ui.components.AddEditItemDialog
import com.example.evim.ui.components.ConfirmDeleteDialog
import com.example.evim.ui.components.ItemCard
import com.example.evim.ui.components.ItemDetailDialog
import com.example.evim.ui.components.MoveItemDialog
import com.example.evim.ui.viewmodel.EvimViewModel
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RoomScreen(
    viewModel: EvimViewModel,
    onNavigateBack: () -> Unit
) {
    val rooms by viewModel.rooms.collectAsState()
    val breadcrumbs by viewModel.breadcrumbs.collectAsState()
    val currentItems by viewModel.currentLevelItems.collectAsState()
    val isGuestMode by viewModel.isGuestMode.collectAsState()
    val isMultiSelectMode by viewModel.isMultiSelectMode.collectAsState()
    val selectedItemIds by viewModel.selectedItemIds.collectAsState()

    var inRoomSearch by remember { mutableStateOf("") }
    var sortOrder by remember { mutableIntStateOf(0) } // 0: Default ID, 1: Name A-Z, 2: Price High-Low
    var showSortMenu by remember { mutableStateOf(false) }

    var showAddItemDialog by remember { mutableStateOf(false) }
    var isAddingBox by remember { mutableStateOf(false) }
    var itemToEdit by remember { mutableStateOf<ItemEntity?>(null) }
    var itemToDelete by remember { mutableStateOf<ItemEntity?>(null) }
    var itemForDetail by remember { mutableStateOf<ItemEntity?>(null) }
    var itemToMove by remember { mutableStateOf<ItemEntity?>(null) }
    var showBatchMoveDialog by remember { mutableStateOf(false) }
    var showBatchDeleteDialog by remember { mutableStateOf(false) }

    val scope = rememberCoroutineScope()
    var detailPathText by remember { mutableStateOf("") }

    // Filter and sort items
    val filteredItems = currentItems
        .filter {
            if (inRoomSearch.isBlank()) true
            else it.name.contains(inRoomSearch, ignoreCase = true) ||
                    it.category.contains(inRoomSearch, ignoreCase = true) ||
                    it.tags.contains(inRoomSearch, ignoreCase = true)
        }
        .let { list ->
            when (sortOrder) {
                1 -> list.sortedBy { it.name.lowercase() }
                2 -> list.sortedByDescending { it.price }
                else -> list.sortedBy { it.id }
            }
        }

    val totalRoomValue = currentItems.sumOf { it.price * it.qty }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = breadcrumbs.lastOrNull()?.let { it.itemName ?: it.roomName } ?: "Oda",
                        fontWeight = FontWeight.Bold,
                        fontSize = 19.sp
                    )
                },
                navigationIcon = {
                    IconButton(
                        onClick = {
                            if (!viewModel.navigateUp()) {
                                onNavigateBack()
                            }
                        },
                        modifier = Modifier.testTag("room_screen_back_button")
                    ) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Geri")
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.toggleMultiSelectMode() }) {
                        Text("☑️", fontSize = 18.sp)
                    }

                    Box {
                        IconButton(onClick = { showSortMenu = true }) {
                            Text("⇅", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                        }
                        DropdownMenu(
                            expanded = showSortMenu,
                            onDismissRequest = { showSortMenu = false }
                        ) {
                            DropdownMenuItem(
                                text = { Text("Ekleme Sırası") },
                                onClick = {
                                    sortOrder = 0
                                    showSortMenu = false
                                }
                            )
                            DropdownMenuItem(
                                text = { Text("İsim (A-Z)") },
                                onClick = {
                                    sortOrder = 1
                                    showSortMenu = false
                                }
                            )
                            DropdownMenuItem(
                                text = { Text("Fiyat (En Yüksek)") },
                                onClick = {
                                    sortOrder = 2
                                    showSortMenu = false
                                }
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.surface)
            )
        },
        floatingActionButton = {
            if (!isGuestMode && !isMultiSelectMode) {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    FloatingActionButton(
                        onClick = {
                            isAddingBox = true
                            showAddItemDialog = true
                        },
                        containerColor = MaterialTheme.colorScheme.secondary,
                        contentColor = Color.White,
                        modifier = Modifier.testTag("add_box_fab")
                    ) {
                        Row(modifier = Modifier.padding(horizontal = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                            Text("📦 Kutu Ekle", fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                        }
                    }

                    FloatingActionButton(
                        onClick = {
                            isAddingBox = false
                            showAddItemDialog = true
                        },
                        containerColor = MaterialTheme.colorScheme.primary,
                        contentColor = Color.White,
                        modifier = Modifier.testTag("add_item_fab")
                    ) {
                        Row(modifier = Modifier.padding(horizontal = 14.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Add, contentDescription = null)
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Eşya Ekle", fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                        }
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
            // Interactive Breadcrumb Navigation
            if (breadcrumbs.isNotEmpty()) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                        .horizontalScroll(rememberScrollState())
                        .padding(horizontal = 16.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    breadcrumbs.forEachIndexed { index, crumb ->
                        val isLast = index == breadcrumbs.size - 1
                        Text(
                            text = crumb.itemName ?: crumb.roomName,
                            fontSize = 13.sp,
                            fontWeight = if (isLast) FontWeight.Bold else FontWeight.Medium,
                            color = if (isLast) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier
                                .clip(RoundedCornerShape(4.dp))
                                .clickable(enabled = !isLast) {
                                    viewModel.navigateToBreadcrumb(index)
                                }
                                .padding(horizontal = 4.dp, vertical = 2.dp)
                        )
                        if (!isLast) {
                            Text(
                                text = " › ",
                                fontSize = 14.sp,
                                color = MaterialTheme.colorScheme.outline
                            )
                        }
                    }
                }
            }

            // Multi-Select Action Bar
            if (isMultiSelectMode) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    )
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = "${selectedItemIds.size} eşya seçildi",
                            fontWeight = FontWeight.SemiBold,
                            fontSize = 14.sp
                        )

                        Row(verticalAlignment = Alignment.CenterVertically) {
                            TextButton(onClick = { viewModel.selectAllCurrentItems() }) {
                                Text("Tümü")
                            }
                            if (selectedItemIds.isNotEmpty()) {
                                IconButton(onClick = { showBatchMoveDialog = true }) {
                                    Text("➡️", fontSize = 16.sp)
                                }
                                IconButton(onClick = { showBatchDeleteDialog = true }) {
                                    Icon(Icons.Default.Delete, contentDescription = "Sil", tint = MaterialTheme.colorScheme.error)
                                }
                            }
                            IconButton(onClick = { viewModel.clearSelection() }) {
                                Icon(Icons.Default.Close, contentDescription = "Kapat")
                            }
                        }
                    }
                }
            }

            // In-room Search
            OutlinedTextField(
                value = inRoomSearch,
                onValueChange = { inRoomSearch = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 6.dp),
                placeholder = { Text("Bu odadaki eşyalarda ara...") },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                singleLine = true,
                shape = RoundedCornerShape(12.dp)
            )

            // Total Value and Count Header
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "${filteredItems.size} Eşya",
                    fontSize = 13.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontWeight = FontWeight.Medium
                )
                if (totalRoomValue > 0) {
                    Text(
                        text = "Toplam: ${totalRoomValue.toInt()} ₺",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            }

            // Item List
            if (filteredItems.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(32.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = if (inRoomSearch.isNotBlank()) "Aramaya uygun eşya bulunamadı."
                        else "Bu alanda henüz eşya yok.\n'Eşya Ekle' veya 'Kutu Ekle'ye dokunun.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontSize = 14.sp
                    )
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(filteredItems, key = { it.id }) { item ->
                        var childrenCount by remember { mutableIntStateOf(0) }
                        scope.launch {
                            childrenCount = viewModel.repository.getChildrenCount(item.id)
                        }

                        ItemCard(
                            item = item,
                            childrenCount = childrenCount,
                            isGuestMode = isGuestMode,
                            isMultiSelectMode = isMultiSelectMode,
                            isSelected = selectedItemIds.contains(item.id),
                            onSelectToggle = { viewModel.toggleItemSelection(item.id) },
                            onClick = {
                                scope.launch {
                                    detailPathText = viewModel.repository.buildFullBreadcrumb(item)
                                    itemForDetail = item
                                }
                            },
                            onEnterChildren = {
                                viewModel.enterChildItem(item)
                            },
                            onDetail = {
                                scope.launch {
                                    detailPathText = viewModel.repository.buildFullBreadcrumb(item)
                                    itemForDetail = item
                                }
                            },
                            onEdit = { itemToEdit = item },
                            onMove = { itemToMove = item },
                            onEmptyBox = { viewModel.emptyBox(item) },
                            onDelete = { itemToDelete = item }
                        )
                    }

                    item {
                        Spacer(modifier = Modifier.height(72.dp))
                    }
                }
            }
        }
    }

    // Dialogs
    if (showAddItemDialog) {
        AddEditItemDialog(
            isBox = isAddingBox,
            onDismiss = { showAddItemDialog = false },
            onSave = { name, cat, note, price, exp, loan, qty, min, unit, tags, fav, sell, lost, move, photo ->
                viewModel.addItem(name, cat, note, price, exp, loan, qty, min, unit, tags, fav, sell, lost, move, photo)
                showAddItemDialog = false
            }
        )
    }

    if (itemToEdit != null) {
        AddEditItemDialog(
            initialItem = itemToEdit,
            onDismiss = { itemToEdit = null },
            onSave = { name, cat, note, price, exp, loan, qty, min, unit, tags, fav, sell, lost, move, photo ->
                viewModel.updateItem(
                    itemToEdit!!.copy(
                        name = name,
                        category = cat,
                        note = note,
                        price = price,
                        expiry = exp,
                        loanedTo = loan,
                        qty = qty,
                        qtyMin = min,
                        unit = unit,
                        tags = tags,
                        isFavorite = fav,
                        isSell = sell,
                        isLost = lost,
                        moveNo = move,
                        photoPath = photo
                    )
                )
                itemToEdit = null
            }
        )
    }

    if (itemToDelete != null) {
        ConfirmDeleteDialog(
            title = "Eşyayı Sil",
            message = "'${itemToDelete!!.name}' silinsin mi?\n(Silinenler geçmişinden geri getirebilirsiniz)",
            onDismiss = { itemToDelete = null },
            onConfirm = {
                viewModel.deleteItem(itemToDelete!!)
                itemToDelete = null
            }
        )
    }

    if (itemForDetail != null) {
        ItemDetailDialog(
            item = itemForDetail!!,
            breadcrumbPath = detailPathText,
            onDismiss = { itemForDetail = null },
            onEdit = {
                val item = itemForDetail
                itemForDetail = null
                itemToEdit = item
            }
        )
    }

    if (itemToMove != null) {
        MoveItemDialog(
            rooms = rooms,
            onDismiss = { itemToMove = null },
            onSelectRoom = { targetRoomId ->
                viewModel.batchMoveSelected(targetRoomId, null)
                viewModel.repository.let {
                    scope.launch {
                        it.moveItems(listOf(itemToMove!!.id), targetRoomId, null)
                        itemToMove = null
                    }
                }
            }
        )
    }

    if (showBatchMoveDialog) {
        MoveItemDialog(
            rooms = rooms,
            onDismiss = { showBatchMoveDialog = false },
            onSelectRoom = { targetRoomId ->
                viewModel.batchMoveSelected(targetRoomId, null)
                showBatchMoveDialog = false
            }
        )
    }

    if (showBatchDeleteDialog) {
        ConfirmDeleteDialog(
            title = "Seçilen Eşyaları Sil",
            message = "${selectedItemIds.size} eşya silinsin mi?",
            onDismiss = { showBatchDeleteDialog = false },
            onConfirm = {
                viewModel.batchDeleteSelected()
                showBatchDeleteDialog = false
            }
        )
    }
}
