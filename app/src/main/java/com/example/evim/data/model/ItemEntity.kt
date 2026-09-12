package com.example.evim.data.model

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "items",
    foreignKeys = [
        ForeignKey(
            entity = RoomEntity::class,
            parentColumns = ["id"],
            childColumns = ["roomId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index("roomId"),
        Index("parentId")
    ]
)
data class ItemEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val roomId: Long,
    val parentId: Long? = null,
    val name: String,
    val category: String = "Diğer",
    val note: String = "",
    val price: Double = 0.0,
    val expiry: String = "",
    val loanedTo: String = "",
    val qty: Int = 1,
    val qtyMin: Int = 0,
    val unit: String = "Adet",
    val tags: String = "",
    val isFavorite: Boolean = false,
    val isSell: Boolean = false,
    val isLost: Boolean = false,
    val moveNo: Int = 0,
    val code: String = "",
    val photoPath: String = "",
    val emoji: String = "",
    val createdAt: Long = System.currentTimeMillis()
)
