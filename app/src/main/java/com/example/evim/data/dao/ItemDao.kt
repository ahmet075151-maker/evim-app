package com.example.evim.data.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.evim.data.model.ItemEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ItemDao {
    @Query("SELECT * FROM items ORDER BY id DESC")
    fun getAllItems(): Flow<List<ItemEntity>>

    @Query("SELECT * FROM items WHERE roomId = :roomId AND ((:parentId IS NULL AND parentId IS NULL) OR parentId = :parentId) ORDER BY id ASC")
    fun getItemsInLevel(roomId: Long, parentId: Long?): Flow<List<ItemEntity>>

    @Query("SELECT * FROM items WHERE id = :id")
    suspend fun getItemById(id: Long): ItemEntity?

    @Query("SELECT COUNT(*) FROM items WHERE parentId = :parentId")
    suspend fun getChildrenCount(parentId: Long): Int

    @Query("SELECT * FROM items WHERE parentId = :parentId")
    suspend fun getChildrenOfParent(parentId: Long): List<ItemEntity>

    @Query("SELECT * FROM items WHERE roomId = :roomId")
    suspend fun getItemsByRoomId(roomId: Long): List<ItemEntity>

    @Query("SELECT * FROM items WHERE name LIKE '%' || :query || '%' OR tags LIKE '%' || :query || '%' OR note LIKE '%' || :query || '%' ORDER BY id DESC")
    fun searchItems(query: String): Flow<List<ItemEntity>>

    @Query("SELECT * FROM items WHERE qtyMin > 0 AND qty <= qtyMin ORDER BY (qtyMin - qty) DESC")
    fun getLowStockItems(): Flow<List<ItemEntity>>

    @Query("SELECT * FROM items WHERE isFavorite = 1 ORDER BY id DESC")
    fun getFavoriteItems(): Flow<List<ItemEntity>>

    @Query("SELECT * FROM items WHERE isSell = 1 ORDER BY id DESC")
    fun getForSaleItems(): Flow<List<ItemEntity>>

    @Query("SELECT * FROM items WHERE isLost = 1 ORDER BY id DESC")
    fun getLostItems(): Flow<List<ItemEntity>>

    @Query("SELECT * FROM items WHERE moveNo > 0 ORDER BY moveNo ASC, id ASC")
    fun getMoveItems(): Flow<List<ItemEntity>>

    @Query("SELECT * FROM items ORDER BY id DESC LIMIT :limit")
    fun getRecentItems(limit: Int = 20): Flow<List<ItemEntity>>

    @Query("SELECT * FROM items WHERE category = :category ORDER BY id DESC")
    fun getItemsByCategory(category: String): Flow<List<ItemEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertItem(item: ItemEntity): Long

    @Update
    suspend fun updateItem(item: ItemEntity)

    @Delete
    suspend fun deleteItem(item: ItemEntity)

    @Query("DELETE FROM items WHERE id = :id")
    suspend fun deleteItemById(id: Long)

    @Query("UPDATE items SET roomId = :newRoomId, parentId = :newParentId WHERE id = :itemId")
    suspend fun updateItemLocation(itemId: Long, newRoomId: Long, newParentId: Long?)

    @Query("UPDATE items SET roomId = :roomId, parentId = :newParentId WHERE parentId = :oldParentId")
    suspend fun promoteChildren(oldParentId: Long, newParentId: Long?, roomId: Long)

    @Query("SELECT COUNT(*) FROM items")
    fun getTotalItemCount(): Flow<Int>

    @Query("SELECT COUNT(*) FROM items WHERE roomId = :roomId")
    fun getItemCountInRoom(roomId: Long): Flow<Int>

    @Query("SELECT COALESCE(SUM(price * qty), 0.0) FROM items")
    fun getTotalItemValue(): Flow<Double>
}
