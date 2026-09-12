package com.example.evim.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.sqlite.db.SupportSQLiteDatabase
import com.example.evim.data.dao.HistoryDao
import com.example.evim.data.dao.ItemDao
import com.example.evim.data.dao.RoomDao
import com.example.evim.data.model.HistoryEntity
import com.example.evim.data.model.ItemEntity
import com.example.evim.data.model.RoomEntity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@Database(
    entities = [RoomEntity::class, ItemEntity::class, HistoryEntity::class],
    version = 1,
    exportSchema = false
)
abstract class EvimDatabase : RoomDatabase() {
    abstract fun roomDao(): RoomDao
    abstract fun itemDao(): ItemDao
    abstract fun historyDao(): HistoryDao

    companion object {
        @Volatile
        private var INSTANCE: EvimDatabase? = null

        fun getDatabase(context: Context, scope: CoroutineScope): EvimDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    EvimDatabase::class.java,
                    "evim_database"
                )
                    .addCallback(EvimDatabaseCallback(scope))
                    .fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }

        private class EvimDatabaseCallback(
            private val scope: CoroutineScope
        ) : RoomDatabase.Callback() {
            override fun onCreate(db: SupportSQLiteDatabase) {
                super.onCreate(db)
                INSTANCE?.let { database ->
                    scope.launch(Dispatchers.IO) {
                        populateInitialRooms(database.roomDao())
                    }
                }
            }

            suspend fun populateInitialRooms(roomDao: RoomDao) {
                if (roomDao.getRoomCount() == 0) {
                    roomDao.insertRoom(RoomEntity(name = "Salon", roomType = "salon"))
                    roomDao.insertRoom(RoomEntity(name = "Mutfak", roomType = "mutfak"))
                    roomDao.insertRoom(RoomEntity(name = "Yatak Odası", roomType = "yatak"))
                    roomDao.insertRoom(RoomEntity(name = "Çalışma Odası", roomType = "calisma"))
                    roomDao.insertRoom(RoomEntity(name = "Banyo", roomType = "banyo"))
                    roomDao.insertRoom(RoomEntity(name = "Depo / Kiler", roomType = "depo"))
                }
            }
        }
    }
}
