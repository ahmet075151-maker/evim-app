package com.example.evim.data.model

import androidx.compose.ui.graphics.Color

data class RoomTypeInfo(
    val key: String,
    val label: String,
    val color: Color,
    val abbr: String,
    val keywords: List<String>
)

object EvimConstants {
    val ITEM_CATEGORIES = listOf(
        "Elektronik",
        "Mobilya",
        "Giyim",
        "Kitap/Kırtasiye",
        "Mutfak Eşyası",
        "Dekorasyon",
        "Belge",
        "Diğer"
    )

    fun getCategoryColor(category: String): Color {
        return when (category) {
            "Elektronik" -> Color(0xFF2196F3)
            "Mobilya" -> Color(0xFF795548)
            "Giyim" -> Color(0xFFE91E63)
            "Kitap/Kırtasiye" -> Color(0xFFFF9800)
            "Mutfak Eşyası" -> Color(0xFF4CAF50)
            "Dekorasyon" -> Color(0xFF9C27B0)
            "Belge" -> Color(0xFF607D8B)
            else -> Color(0xFF9E9E9E)
        }
    }

    val UNIT_TYPES = listOf("Adet", "Kutu", "Kg", "Litre", "Paket", "Çuval", "Şişe")

    val ROOM_TYPES = listOf(
        RoomTypeInfo("salon", "Salon", Color(0xFF3F51B5), "SLN", listOf("salon", "oturma", "living")),
        RoomTypeInfo("mutfak", "Mutfak", Color(0xFFFF7043), "MTF", listOf("mutfak", "kitchen", "kiler")),
        RoomTypeInfo("yatak", "Yatak Odası", Color(0xFF7E57C2), "YTK", listOf("yatak", "ebeveyn", "bedroom")),
        RoomTypeInfo("banyo", "Banyo", Color(0xFF26A69A), "BNY", listOf("banyo", "tuvalet", "wc", "lavabo")),
        RoomTypeInfo("calisma", "Çalışma Odası", Color(0xFF42A5F5), "CLS", listOf("calisma", "çalışma", "ofis", "office")),
        RoomTypeInfo("bilgisayar", "Bilgisayar Odası", Color(0xFF29B6F6), "PC", listOf("bilgisayar", "pc", "sistem")),
        RoomTypeInfo("cocuk", "Çocuk Odası", Color(0xFFEC407A), "CCK", listOf("cocuk", "çocuk", "bebek", "baby")),
        RoomTypeInfo("garaj", "Garaj", Color(0xFF78909C), "GRJ", listOf("garaj", "otopark")),
        RoomTypeInfo("bahce", "Bahçe", Color(0xFF66BB6A), "BHC", listOf("bahce", "bahçe", "teras", "deck")),
        RoomTypeInfo("depo", "Depo / Kiler", Color(0xFF8D6E63), "DPO", listOf("depo", "bodrum", "ardiye")),
        RoomTypeInfo("koridor", "Koridor / Antre", Color(0xFFAB47BC), "KRD", listOf("koridor", "antre", "hol", "giriş")),
        RoomTypeInfo("misafir", "Misafir Odası", Color(0xFFFFA726), "MSF", listOf("misafir", "guest")),
        RoomTypeInfo("camasir", "Çamaşır Odası", Color(0xFF26C6DA), "CMS", listOf("camasir", "çamaşır", "ütü")),
        RoomTypeInfo("balkon", "Balkon", Color(0xFF9CCC65), "BLK", listOf("balkon", "veranda")),
        RoomTypeInfo("diger", "Diğer", Color(0xFF78909C), "DGR", emptyList())
    )

    fun getRoomType(key: String): RoomTypeInfo {
        return ROOM_TYPES.find { it.key == key } ?: ROOM_TYPES.last()
    }

    fun inferRoomType(name: String): String {
        val lower = name.lowercase().trim()
        for (rt in ROOM_TYPES) {
            for (kw in rt.keywords) {
                if (lower.contains(kw)) {
                    return rt.key
                }
            }
        }
        return "diger"
    }
}
