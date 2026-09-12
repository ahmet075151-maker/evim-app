package com.example.evim.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "history")
data class HistoryEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val kind: String, // "item" or "room"
    val name: String,
    val pathText: String,
    val deletedAt: String,
    val restoreData: String // JSON payload of item or room
)
