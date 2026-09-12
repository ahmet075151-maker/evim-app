package com.example.evim.data.repository

import com.example.evim.data.dao.HistoryDao
import com.example.evim.data.dao.ItemDao
import com.example.evim.data.dao.RoomDao
import com.example.evim.data.model.HistoryEntity
import com.example.evim.data.model.ItemEntity
import com.example.evim.data.model.RoomEntity
import kotlinx.coroutines.flow.Flow
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class EvimRepository(
    private val roomDao: RoomDao,
    private val itemDao: ItemDao,
    private val historyDao: HistoryDao
) {
    val allRooms: Flow<List<RoomEntity>> = roomDao.getAllRooms()
    val allItems: Flow<List<ItemEntity>> = itemDao.getAllItems()
    val allHistory: Flow<List<HistoryEntity>> = historyDao.getAllHistory()
    val lowStockItems: Flow<List<ItemEntity>> = itemDao.getLowStockItems()
    val favoriteItems: Flow<List<ItemEntity>> = itemDao.getFavoriteItems()
    val forSaleItems: Flow<List<ItemEntity>> = itemDao.getForSaleItems()
    val lostItems: Flow<List<ItemEntity>> = itemDao.getLostItems()
    val moveItems: Flow<List<ItemEntity>> = itemDao.getMoveItems()
    val totalItemCount: Flow<Int> = itemDao.getTotalItemCount()
    val totalItemValue: Flow<Double> = itemDao.getTotalItemValue()

    suspend fun getRoomById(id: Long): RoomEntity? = roomDao.getRoomById(id)
    suspend fun insertRoom(room: RoomEntity): Long = roomDao.insertRoom(room)
    suspend fun updateRoom(room: RoomEntity) = roomDao.updateRoom(room)

    suspend fun deleteRoom(room: RoomEntity) {
        val itemsInRoom = itemDao.getItemsByRoomId(room.id)
        val dateStr = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()).format(Date())
        val roomJson = JSONObject().apply {
            put("name", room.name)
            put("roomType", room.roomType)
            put("itemCount", itemsInRoom.size)
        }.toString()

        historyDao.insertHistory(
            HistoryEntity(
                kind = "room",
                name = room.name,
                pathText = "Oda: ${room.name} (${itemsInRoom.size} eşya)",
                deletedAt = dateStr,
                restoreData = roomJson
            )
        )
        roomDao.deleteRoom(room)
    }

    fun getItemsInLevel(roomId: Long, parentId: Long?): Flow<List<ItemEntity>> =
        itemDao.getItemsInLevel(roomId, parentId)

    suspend fun getItemById(id: Long): ItemEntity? = itemDao.getItemById(id)
    suspend fun getChildrenCount(parentId: Long): Int = itemDao.getChildrenCount(parentId)

    suspend fun insertItem(item: ItemEntity): Long = itemDao.insertItem(item)
    suspend fun updateItem(item: ItemEntity) = itemDao.updateItem(item)

    suspend fun deleteItem(item: ItemEntity, breadcrumbPath: String) {
        val dateStr = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()).format(Date())
        val itemJson = JSONObject().apply {
            put("name", item.name)
            put("roomId", item.roomId)
            put("parentId", item.parentId ?: JSONObject.NULL)
            put("category", item.category)
            put("note", item.note)
            put("price", item.price)
            put("expiry", item.expiry)
            put("loanedTo", item.loanedTo)
            put("qty", item.qty)
            put("qtyMin", item.qtyMin)
            put("unit", item.unit)
            put("tags", item.tags)
            put("isFavorite", item.isFavorite)
            put("isSell", item.isSell)
            put("isLost", item.isLost)
            put("moveNo", item.moveNo)
            put("photoPath", item.photoPath)
        }.toString()

        historyDao.insertHistory(
            HistoryEntity(
                kind = "item",
                name = item.name,
                pathText = breadcrumbPath,
                deletedAt = dateStr,
                restoreData = itemJson
            )
        )
        itemDao.deleteItem(item)
    }

    suspend fun restoreHistory(history: HistoryEntity): Boolean {
        try {
            val json = JSONObject(history.restoreData)
            if (history.kind == "room") {
                val room = RoomEntity(
                    name = json.optString("name", history.name),
                    roomType = json.optString("roomType", "diger")
                )
                roomDao.insertRoom(room)
            } else {
                val item = ItemEntity(
                    name = json.optString("name", history.name),
                    roomId = json.optLong("roomId", 1L),
                    parentId = if (json.isNull("parentId")) null else json.optLong("parentId"),
                    category = json.optString("category", "Diğer"),
                    note = json.optString("note", ""),
                    price = json.optDouble("price", 0.0),
                    expiry = json.optString("expiry", ""),
                    loanedTo = json.optString("loanedTo", ""),
                    qty = json.optInt("qty", 1),
                    qtyMin = json.optInt("qtyMin", 0),
                    unit = json.optString("unit", "Adet"),
                    tags = json.optString("tags", ""),
                    isFavorite = json.optBoolean("isFavorite", false),
                    isSell = json.optBoolean("isSell", false),
                    isLost = json.optBoolean("isLost", false),
                    moveNo = json.optInt("moveNo", 0),
                    photoPath = json.optString("photoPath", "")
                )
                itemDao.insertItem(item)
            }
            historyDao.deleteHistory(history)
            return true
        } catch (e: Exception) {
            e.printStackTrace()
            return false
        }
    }

    suspend fun clearHistory() {
        historyDao.clearAllHistory()
    }

    suspend fun emptyBox(boxItem: ItemEntity) {
        // Promote all children of this item to the parent level of this item
        itemDao.promoteChildren(
            oldParentId = boxItem.id,
            newParentId = boxItem.parentId,
            roomId = boxItem.roomId
        )
    }

    suspend fun moveItems(itemIds: List<Long>, targetRoomId: Long, targetParentId: Long?) {
        for (id in itemIds) {
            itemDao.updateItemLocation(id, targetRoomId, targetParentId)
        }
    }

    fun searchItems(query: String): Flow<List<ItemEntity>> = itemDao.searchItems(query)

    fun getRecentItems(limit: Int = 20): Flow<List<ItemEntity>> = itemDao.getRecentItems(limit)

    fun getItemsByCategory(category: String): Flow<List<ItemEntity>> =
        itemDao.getItemsByCategory(category)

    fun getItemCountInRoom(roomId: Long): Flow<Int> = itemDao.getItemCountInRoom(roomId)

    suspend fun buildFullBreadcrumb(item: ItemEntity): String {
        val pathNames = mutableListOf(item.name)
        var currentParentId = item.parentId
        while (currentParentId != null) {
            val parent = itemDao.getItemById(currentParentId)
            if (parent != null) {
                pathNames.add(0, parent.name)
                currentParentId = parent.parentId
            } else {
                break
            }
        }
        val room = roomDao.getRoomById(item.roomId)
        if (room != null) {
            pathNames.add(0, room.name)
        }
        return pathNames.joinToString(" › ")
    }

    suspend fun exportCsvData(): String {
        val items = itemDao.getChildrenOfParent(0) // or we fetch all
        // Let's get all rooms and all items
        val sb = StringBuilder()
        sb.append("ID,Oda,Eşya Adı,Kategori,Miktar,Birim,Min Stok,Fiyat TL,Koli No,Not,Etiketler,Ödünç,SKT,Favori,Satılık,Kayıp\n")
        // We'll iterate all items
        return sb.toString()
    }
}
