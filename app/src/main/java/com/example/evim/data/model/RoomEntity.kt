package com.example.evim.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "rooms")
data class RoomEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val name: String,
    val roomType: String = "diger",
    val emoji: String = "",
    val photoPath: String = ""
)
