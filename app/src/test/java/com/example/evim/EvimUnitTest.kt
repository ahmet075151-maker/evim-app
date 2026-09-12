package com.example.evim

import com.example.evim.data.model.EvimConstants
import com.example.evim.data.model.ItemEntity
import com.example.evim.data.model.RoomEntity
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test

class EvimUnitTest {

    @Test
    fun testRoomTypeInference() {
        assertEquals("salon", EvimConstants.inferRoomType("Büyük Salon"))
        assertEquals("mutfak", EvimConstants.inferRoomType("Amerikan Mutfak"))
        assertEquals("yatak", EvimConstants.inferRoomType("Ebeveyn Yatak Odası"))
        assertEquals("banyo", EvimConstants.inferRoomType("Misafir Banyosu"))
        assertEquals("depo", EvimConstants.inferRoomType("Arka Depo"))
        assertEquals("diger", EvimConstants.inferRoomType("Özel Oda XYZ"))
    }

    @Test
    fun testCategoryColors() {
        assertNotNull(EvimConstants.getCategoryColor("Elektronik"))
        assertNotNull(EvimConstants.getCategoryColor("Mobilya"))
        assertNotNull(EvimConstants.getCategoryColor("Mutfak Eşyası"))
        assertNotNull(EvimConstants.getCategoryColor("Bilinmeyen"))
    }

    @Test
    fun testRoomTypeLookup() {
        val salon = EvimConstants.getRoomType("salon")
        assertEquals("Salon", salon.label)
        assertEquals("SLN", salon.abbr)

        val mutfak = EvimConstants.getRoomType("mutfak")
        assertEquals("Mutfak", mutfak.label)
        assertEquals("MTF", mutfak.abbr)
    }

    @Test
    fun testItemEntityCreation() {
        val item = ItemEntity(
            id = 1L,
            roomId = 2L,
            name = "Test Eşyası",
            category = "Elektronik",
            price = 150.0,
            qty = 3,
            unit = "Adet"
        )
        assertEquals("Test Eşyası", item.name)
        assertEquals(150.0, item.price, 0.001)
        assertEquals(3, item.qty)
    }
}
