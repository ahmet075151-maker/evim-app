package com.example.evim.ui.viewmodel

import android.app.Application
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.widget.Toast
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.evim.data.db.EvimDatabase
import com.example.evim.data.model.HistoryEntity
import com.example.evim.data.model.ItemEntity
import com.example.evim.data.model.RoomEntity
import com.example.evim.data.repository.EvimRepository
import com.example.evim.ui.theme.EvimThemeMode
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class BreadcrumbStep(
    val roomId: Long,
    val roomName: String,
    val itemId: Long? = null,
    val itemName: String? = null
)

class EvimViewModel(application: Application) : AndroidViewModel(application) {
    private val database = EvimDatabase.getDatabase(application, viewModelScope)
    val repository = EvimRepository(database.roomDao(), database.itemDao(), database.historyDao())

    val rooms: StateFlow<List<RoomEntity>> = repository.allRooms
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val allItems: StateFlow<List<ItemEntity>> = repository.allItems
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val totalCount: StateFlow<Int> = repository.totalItemCount
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), 0)

    val totalValue: StateFlow<Double> = repository.totalItemValue
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), 0.0)

    val lowStockItems: StateFlow<List<ItemEntity>> = repository.lowStockItems
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val history: StateFlow<List<HistoryEntity>> = repository.allHistory
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    // Guest Mode
    private val _isGuestMode = MutableStateFlow(false)
    val isGuestMode: StateFlow<Boolean> = _isGuestMode.asStateFlow()

    // Theme Mode
    private val _currentTheme = MutableStateFlow(EvimThemeMode.TURUNCU)
    val currentTheme: StateFlow<EvimThemeMode> = _currentTheme.asStateFlow()

    // Current navigation state inside a room
    private val _currentRoomId = MutableStateFlow<Long?>(null)
    val currentRoomId: StateFlow<Long?> = _currentRoomId.asStateFlow()

    private val _currentParentId = MutableStateFlow<Long?>(null)
    val currentParentId: StateFlow<Long?> = _currentParentId.asStateFlow()

    private val _breadcrumbs = MutableStateFlow<List<BreadcrumbStep>>(emptyList())
    val breadcrumbs: StateFlow<List<BreadcrumbStep>> = _breadcrumbs.asStateFlow()

    // Room items reactive flow
    val currentLevelItems: StateFlow<List<ItemEntity>> = combine(
        _currentRoomId,
        _currentParentId
    ) { roomId, parentId ->
        Pair(roomId, parentId)
    }.flatMapLatest { (roomId, parentId) ->
        if (roomId != null) {
            repository.getItemsInLevel(roomId, parentId)
        } else {
            MutableStateFlow(emptyList())
        }
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    // Multi-selection state
    private val _isMultiSelectMode = MutableStateFlow(false)
    val isMultiSelectMode: StateFlow<Boolean> = _isMultiSelectMode.asStateFlow()

    private val _selectedItemIds = MutableStateFlow<Set<Long>>(emptySet())
    val selectedItemIds: StateFlow<Set<Long>> = _selectedItemIds.asStateFlow()

    // Search
    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    val searchResults: StateFlow<List<ItemEntity>> = _searchQuery.flatMapLatest { q ->
        if (q.isBlank()) MutableStateFlow(emptyList())
        else repository.searchItems(q.trim())
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun toggleGuestMode() {
        _isGuestMode.value = !_isGuestMode.value
    }

    fun setTheme(theme: EvimThemeMode) {
        _currentTheme.value = theme
    }

    fun setSearchQuery(query: String) {
        _searchQuery.value = query
    }

    fun enterRoom(room: RoomEntity) {
        _currentRoomId.value = room.id
        _currentParentId.value = null
        _breadcrumbs.value = listOf(BreadcrumbStep(roomId = room.id, roomName = room.name))
        clearSelection()
    }

    fun enterChildItem(item: ItemEntity) {
        _currentParentId.value = item.id
        val currentCrumbs = _breadcrumbs.value.toMutableList()
        val roomId = _currentRoomId.value ?: item.roomId
        val roomName = currentCrumbs.firstOrNull()?.roomName ?: "Oda"
        currentCrumbs.add(BreadcrumbStep(roomId = roomId, roomName = roomName, itemId = item.id, itemName = item.name))
        _breadcrumbs.value = currentCrumbs
        clearSelection()
    }

    fun navigateToBreadcrumb(index: Int) {
        val crumbs = _breadcrumbs.value
        if (index in crumbs.indices) {
            val target = crumbs[index]
            _currentRoomId.value = target.roomId
            _currentParentId.value = target.itemId
            _breadcrumbs.value = crumbs.subList(0, index + 1)
            clearSelection()
        }
    }

    fun navigateUp(): Boolean {
        val crumbs = _breadcrumbs.value
        if (crumbs.size > 1) {
            val newCrumbs = crumbs.dropLast(1)
            val top = newCrumbs.last()
            _currentRoomId.value = top.roomId
            _currentParentId.value = top.itemId
            _breadcrumbs.value = newCrumbs
            clearSelection()
            return true
        }
        return false
    }

    // Room Actions
    fun addRoom(name: String, roomType: String) {
        viewModelScope.launch {
            repository.insertRoom(RoomEntity(name = name, roomType = roomType))
        }
    }

    fun updateRoom(room: RoomEntity) {
        viewModelScope.launch {
            repository.updateRoom(room)
        }
    }

    fun deleteRoom(room: RoomEntity) {
        viewModelScope.launch {
            repository.deleteRoom(room)
        }
    }

    // Item Actions
    fun addItem(
        name: String,
        category: String,
        note: String,
        price: Double,
        expiry: String,
        loanedTo: String,
        qty: Int,
        qtyMin: Int,
        unit: String,
        tags: String,
        isFavorite: Boolean,
        isSell: Boolean,
        isLost: Boolean,
        moveNo: Int,
        photoPath: String
    ) {
        val roomId = _currentRoomId.value ?: return
        val parentId = _currentParentId.value
        viewModelScope.launch {
            repository.insertItem(
                ItemEntity(
                    roomId = roomId,
                    parentId = parentId,
                    name = name,
                    category = category,
                    note = note,
                    price = price,
                    expiry = expiry,
                    loanedTo = loanedTo,
                    qty = qty,
                    qtyMin = qtyMin,
                    unit = unit,
                    tags = tags,
                    isFavorite = isFavorite,
                    isSell = isSell,
                    isLost = isLost,
                    moveNo = moveNo,
                    photoPath = photoPath
                )
            )
        }
    }

    fun updateItem(item: ItemEntity) {
        viewModelScope.launch {
            repository.updateItem(item)
        }
    }

    fun deleteItem(item: ItemEntity) {
        viewModelScope.launch {
            val path = repository.buildFullBreadcrumb(item)
            repository.deleteItem(item, path)
        }
    }

    fun emptyBox(boxItem: ItemEntity) {
        viewModelScope.launch {
            repository.emptyBox(boxItem)
        }
    }

    // Selection & Batch Actions
    fun toggleMultiSelectMode() {
        _isMultiSelectMode.value = !_isMultiSelectMode.value
        if (!_isMultiSelectMode.value) {
            _selectedItemIds.value = emptySet()
        }
    }

    fun toggleItemSelection(id: Long) {
        val set = _selectedItemIds.value.toMutableSet()
        if (set.contains(id)) {
            set.remove(id)
        } else {
            set.add(id)
        }
        _selectedItemIds.value = set
        if (set.isNotEmpty()) {
            _isMultiSelectMode.value = true
        }
    }

    fun selectAllCurrentItems() {
        val current = currentLevelItems.value.map { it.id }.toSet()
        _selectedItemIds.value = current
        _isMultiSelectMode.value = true
    }

    fun clearSelection() {
        _selectedItemIds.value = emptySet()
        _isMultiSelectMode.value = false
    }

    fun batchDeleteSelected() {
        val selected = _selectedItemIds.value.toList()
        viewModelScope.launch {
            for (id in selected) {
                val item = repository.getItemById(id)
                if (item != null) {
                    val path = repository.buildFullBreadcrumb(item)
                    repository.deleteItem(item, path)
                }
            }
            clearSelection()
        }
    }

    fun batchMoveSelected(targetRoomId: Long, targetParentId: Long?) {
        val selected = _selectedItemIds.value.toList()
        viewModelScope.launch {
            repository.moveItems(selected, targetRoomId, targetParentId)
            clearSelection()
        }
    }

    // History Actions
    fun restoreHistory(history: HistoryEntity) {
        viewModelScope.launch {
            repository.restoreHistory(history)
        }
    }

    fun clearAllHistory() {
        viewModelScope.launch {
            repository.clearHistory()
        }
    }

    fun copyShoppingList(context: Context) {
        viewModelScope.launch {
            val list = lowStockItems.value
            if (list.isEmpty()) {
                Toast.makeText(context, "Stoğu azalan ürün yok.", Toast.LENGTH_SHORT).show()
                return@launch
            }
            val sb = StringBuilder()
            sb.append("🛒 EVİM - ALIŞVERİŞ LİSTESİ\n")
            list.forEach { item ->
                val missing = (item.qtyMin - item.qty).coerceAtLeast(1)
                sb.append("• ${item.name} (${missing} ${item.unit} eksik - Mevcut: ${item.qty})\n")
            }
            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("Alışveriş Listesi", sb.toString())
            clipboard.setPrimaryClip(clip)
            Toast.makeText(context, "Alışveriş listesi kopyalandı!", Toast.LENGTH_SHORT).show()
        }
    }

    fun copyExportData(context: Context) {
        viewModelScope.launch {
            val items = allItems.value
            val sb = StringBuilder()
            sb.append("ID,Oda ID,Eşya,Kategori,Adet,Birim,Min Stok,Fiyat TL,Koli No,Not\n")
            items.forEach {
                sb.append("${it.id},${it.roomId},\"${it.name}\",\"${it.category}\",${it.qty},${it.unit},${it.qtyMin},${it.price},${it.moveNo},\"${it.note}\"\n")
            }
            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("Evim Envanter CSV", sb.toString())
            clipboard.setPrimaryClip(clip)
            Toast.makeText(context, "Envanter CSV panoya kopyalandı!", Toast.LENGTH_SHORT).show()
        }
    }
}
