package com.example.evim.ui.components

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.core.content.FileProvider
import coil.compose.AsyncImage
import com.example.evim.data.model.EvimConstants
import com.example.evim.data.model.ItemEntity
import com.example.evim.data.model.RoomEntity
import com.example.evim.ui.theme.EvimThemeMode
import java.io.File
import java.io.FileOutputStream

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddEditRoomDialog(
    initialRoom: RoomEntity? = null,
    onDismiss: () -> Unit,
    onSave: (name: String, roomType: String) -> Unit
) {
    var name by remember { mutableStateOf(initialRoom?.name ?: "") }
    var selectedType by remember { mutableStateOf(initialRoom?.roomType ?: "salon") }
    var expanded by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = if (initialRoom != null) "Odayı Düzenle" else "Yeni Oda Ekle",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
        },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                OutlinedTextField(
                    value = name,
                    onValueChange = {
                        name = it
                        if (initialRoom == null) {
                            val guessed = EvimConstants.inferRoomType(it)
                            if (guessed != "diger") {
                                selectedType = guessed
                            }
                        }
                    },
                    label = { Text("Oda Adı") },
                    placeholder = { Text("Örn: Salon, Mutfak") },
                    singleLine = true,
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("room_name_input")
                )

                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = it }
                ) {
                    val currentTypeInfo = EvimConstants.getRoomType(selectedType)
                    OutlinedTextField(
                        value = currentTypeInfo.label,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Oda Türü") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                        modifier = Modifier
                            .menuAnchor()
                            .fillMaxWidth()
                    )
                    ExposedDropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false }
                    ) {
                        EvimConstants.ROOM_TYPES.forEach { rt ->
                            DropdownMenuItem(
                                text = {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Box(
                                            modifier = Modifier
                                                .size(16.dp)
                                                .clip(CircleShape)
                                                .background(rt.color)
                                        )
                                        Spacer(modifier = Modifier.width(8.dp))
                                        Text(rt.label)
                                    }
                                },
                                onClick = {
                                    selectedType = rt.key
                                    expanded = false
                                }
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    if (name.isNotBlank()) {
                        onSave(name.trim(), selectedType)
                    }
                },
                enabled = name.isNotBlank(),
                modifier = Modifier.testTag("save_room_button")
            ) {
                Text(if (initialRoom != null) "Güncelle" else "Ekle")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("İptal")
            }
        }
    )
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun AddEditItemDialog(
    initialItem: ItemEntity? = null,
    isBox: Boolean = false,
    onDismiss: () -> Unit,
    onSave: (
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
    ) -> Unit
) {
    val context = LocalContext.current
    var name by remember { mutableStateOf(initialItem?.name ?: "") }
    var category by remember { mutableStateOf(initialItem?.category ?: (if (isBox) "Diğer" else EvimConstants.ITEM_CATEGORIES.first())) }
    var note by remember { mutableStateOf(initialItem?.note ?: "") }
    var priceText by remember { mutableStateOf(initialItem?.price?.takeIf { it > 0 }?.toString() ?: "") }
    var expiry by remember { mutableStateOf(initialItem?.expiry ?: "") }
    var loanedTo by remember { mutableStateOf(initialItem?.loanedTo ?: "") }
    var qtyText by remember { mutableStateOf(initialItem?.qty?.toString() ?: "1") }
    var qtyMinText by remember { mutableStateOf(initialItem?.qtyMin?.takeIf { it > 0 }?.toString() ?: "") }
    var unit by remember { mutableStateOf(initialItem?.unit ?: "Adet") }
    var tags by remember { mutableStateOf(initialItem?.tags ?: "") }
    var moveNoText by remember { mutableStateOf(initialItem?.moveNo?.takeIf { it > 0 }?.toString() ?: "") }
    var isFavorite by remember { mutableStateOf(initialItem?.isFavorite ?: false) }
    var isSell by remember { mutableStateOf(initialItem?.isSell ?: false) }
    var isLost by remember { mutableStateOf(initialItem?.isLost ?: false) }
    var photoPath by remember { mutableStateOf(initialItem?.photoPath ?: "") }

    var categoryExpanded by remember { mutableStateOf(false) }
    var unitExpanded by remember { mutableStateOf(false) }

    // Camera capture state
    var tempCameraUri by remember { mutableStateOf<Uri?>(null) }
    var tempCameraFile by remember { mutableStateOf<File?>(null) }

    val cameraLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture()
    ) { success ->
        if (success && tempCameraFile != null && tempCameraFile!!.exists()) {
            photoPath = tempCameraFile!!.absolutePath
        }
    }

    val photoPickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickVisualMedia()
    ) { uri ->
        if (uri != null) {
            try {
                val picturesDir = File(context.filesDir, "item_photos")
                if (!picturesDir.exists()) picturesDir.mkdirs()
                val destFile = File(picturesDir, "photo_${System.currentTimeMillis()}.jpg")
                context.contentResolver.openInputStream(uri)?.use { input ->
                    FileOutputStream(destFile).use { output ->
                        input.copyTo(output)
                    }
                }
                photoPath = destFile.absolutePath
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(
            modifier = Modifier
                .fillMaxWidth(0.95f)
                .padding(vertical = 24.dp),
            shape = RoundedCornerShape(24.dp),
            color = MaterialTheme.colorScheme.surface,
            tonalElevation = 6.dp
        ) {
            Column(
                modifier = Modifier
                    .padding(20.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = when {
                            initialItem != null -> "Eşyayı Düzenle"
                            isBox -> "Yeni Kutu / Depo Ekle"
                            else -> "Yeni Eşya Ekle"
                        },
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold
                    )
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, contentDescription = "Kapat")
                    }
                }

                // Name
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text(if (isBox) "Kutu / Depo Adı" else "Eşya Adı") },
                    placeholder = { Text(if (isBox) "Örn: Koli 1, Gardırop Üst Kutu" else "Örn: Kitap, HDMI Kablosu") },
                    singleLine = true,
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("item_name_input")
                )

                // Category & Unit row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    ExposedDropdownMenuBox(
                        expanded = categoryExpanded,
                        onExpandedChange = { categoryExpanded = it },
                        modifier = Modifier.weight(1f)
                    ) {
                        OutlinedTextField(
                            value = category,
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Kategori") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = categoryExpanded) },
                            modifier = Modifier.menuAnchor()
                        )
                        ExposedDropdownMenu(
                            expanded = categoryExpanded,
                            onDismissRequest = { categoryExpanded = false }
                        ) {
                            EvimConstants.ITEM_CATEGORIES.forEach { cat ->
                                DropdownMenuItem(
                                    text = {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            Box(
                                                modifier = Modifier
                                                    .size(12.dp)
                                                    .clip(CircleShape)
                                                    .background(EvimConstants.getCategoryColor(cat))
                                            )
                                            Spacer(modifier = Modifier.width(8.dp))
                                            Text(cat)
                                        }
                                    },
                                    onClick = {
                                        category = cat
                                        categoryExpanded = false
                                    }
                                )
                            }
                        }
                    }

                    ExposedDropdownMenuBox(
                        expanded = unitExpanded,
                        onExpandedChange = { unitExpanded = it },
                        modifier = Modifier.weight(1f)
                    ) {
                        OutlinedTextField(
                            value = unit,
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Birim") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = unitExpanded) },
                            modifier = Modifier.menuAnchor()
                        )
                        ExposedDropdownMenu(
                            expanded = unitExpanded,
                            onDismissRequest = { unitExpanded = false }
                        ) {
                            EvimConstants.UNIT_TYPES.forEach { u ->
                                DropdownMenuItem(
                                    text = { Text(u) },
                                    onClick = {
                                        unit = u
                                        unitExpanded = false
                                    }
                                )
                            }
                        }
                    }
                }

                // Quantity & Min Quantity
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutlinedTextField(
                        value = qtyText,
                        onValueChange = { qtyText = it.filter { c -> c.isDigit() } },
                        label = { Text("Miktar") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f)
                    )
                    OutlinedTextField(
                        value = qtyMinText,
                        onValueChange = { qtyMinText = it.filter { c -> c.isDigit() } },
                        label = { Text("Min. Stok Uyarısı") },
                        placeholder = { Text("Örn: 2") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f)
                    )
                }

                // Price & Move No
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutlinedTextField(
                        value = priceText,
                        onValueChange = { priceText = it },
                        label = { Text("Değer (TL)") },
                        placeholder = { Text("0") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        modifier = Modifier.weight(1f)
                    )
                    OutlinedTextField(
                        value = moveNoText,
                        onValueChange = { moveNoText = it.filter { c -> c.isDigit() } },
                        label = { Text("Koli No (Taşınma)") },
                        placeholder = { Text("Örn: 1") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f)
                    )
                }

                // Expiry & Loaned To
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutlinedTextField(
                        value = expiry,
                        onValueChange = { raw ->
                            val digits = raw.filter { it.isDigit() }.take(8)
                            val sb = StringBuilder()
                            for (i in digits.indices) {
                                if (i == 2 || i == 4) sb.append('/')
                                sb.append(digits[i])
                            }
                            expiry = sb.toString()
                        },
                        label = { Text("Son Kul. / Garanti") },
                        placeholder = { Text("GG/AA/YYYY") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f)
                    )
                    OutlinedTextField(
                        value = loanedTo,
                        onValueChange = { loanedTo = it },
                        label = { Text("Ödünç Verildiyse") },
                        placeholder = { Text("Kime?") },
                        singleLine = true,
                        modifier = Modifier.weight(1f)
                    )
                }

                // Note & Tags
                OutlinedTextField(
                    value = note,
                    onValueChange = { note = it },
                    label = { Text("Not (İsteğe bağlı)") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = tags,
                    onValueChange = { tags = it },
                    label = { Text("Etiketler (Virgülle ayırın)") },
                    placeholder = { Text("kablo, şarj, salon") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )

                // Status Filter Chips
                Text("Durum Etiketleri:", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
                FlowRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    FilterChip(
                        selected = isFavorite,
                        onClick = { isFavorite = !isFavorite },
                        label = { Text("⭐ Favori") },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = Color(0xFFFFB300).copy(alpha = 0.2f),
                            selectedLabelColor = Color(0xFFFF8F00)
                        )
                    )
                    FilterChip(
                        selected = isSell,
                        onClick = { isSell = !isSell },
                        label = { Text("🏷️ Satılık") },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = Color(0xFF4CAF50).copy(alpha = 0.2f),
                            selectedLabelColor = Color(0xFF2E7D32)
                        )
                    )
                    FilterChip(
                        selected = isLost,
                        onClick = { isLost = !isLost },
                        label = { Text("❓ Kayıp") },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = Color(0xFFF44336).copy(alpha = 0.2f),
                            selectedLabelColor = Color(0xFFC62828)
                        )
                    )
                }

                // Photo preview and pickers
                Text("Fotoğraf:", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(64.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(MaterialTheme.colorScheme.surfaceVariant),
                        contentAlignment = Alignment.Center
                    ) {
                        if (photoPath.isNotBlank() && File(photoPath).exists()) {
                            AsyncImage(
                                model = File(photoPath),
                                contentDescription = "Fotoğraf",
                                modifier = Modifier
                                    .size(64.dp)
                                    .clip(RoundedCornerShape(12.dp)),
                                contentScale = ContentScale.Crop
                            )
                        } else {
                            Text(
                                text = "Foto Yok",
                                fontSize = 10.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }

                    OutlinedButton(
                        onClick = {
                            photoPickerLauncher.launch(
                                PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)
                            )
                        }
                    ) {
                        Text("🖼️ Galeri", fontSize = 13.sp)
                    }

                    OutlinedButton(
                        onClick = {
                            try {
                                val picturesDir = File(context.filesDir, "item_photos")
                                if (!picturesDir.exists()) picturesDir.mkdirs()
                                val file = File(picturesDir, "cam_${System.currentTimeMillis()}.jpg")
                                tempCameraFile = file
                                val uri = FileProvider.getUriForFile(
                                    context,
                                    "${context.packageName}.fileprovider",
                                    file
                                )
                                tempCameraUri = uri
                                cameraLauncher.launch(uri)
                            } catch (e: Exception) {
                                e.printStackTrace()
                            }
                        }
                    ) {
                        Text("📷 Kamera", fontSize = 13.sp)
                    }

                    if (photoPath.isNotBlank()) {
                        IconButton(onClick = { photoPath = "" }) {
                            Icon(Icons.Default.Close, contentDescription = "Fotoğrafı Kaldır", tint = MaterialTheme.colorScheme.error)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                // Action Buttons
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    TextButton(onClick = onDismiss) {
                        Text("İptal")
                    }
                    Spacer(modifier = Modifier.width(8.dp))
                    Button(
                        onClick = {
                            if (name.isNotBlank()) {
                                onSave(
                                    name.trim(),
                                    category,
                                    note.trim(),
                                    priceText.toDoubleOrNull() ?: 0.0,
                                    expiry.trim(),
                                    loanedTo.trim(),
                                    qtyText.toIntOrNull() ?: 1,
                                    qtyMinText.toIntOrNull() ?: 0,
                                    unit,
                                    tags.trim(),
                                    isFavorite,
                                    isSell,
                                    isLost,
                                    moveNoText.toIntOrNull() ?: 0,
                                    photoPath
                                )
                            }
                        },
                        enabled = name.isNotBlank(),
                        modifier = Modifier.testTag("save_item_button")
                    ) {
                        Text("Kaydet")
                    }
                }
            }
        }
    }
}

@Composable
fun ItemDetailDialog(
    item: ItemEntity,
    breadcrumbPath: String,
    onDismiss: () -> Unit,
    onEdit: () -> Unit
) {
    val categoryColor = EvimConstants.getCategoryColor(item.category)

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = item.name,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
        },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                if (item.photoPath.isNotBlank() && File(item.photoPath).exists()) {
                    AsyncImage(
                        model = File(item.photoPath),
                        contentDescription = item.name,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(180.dp)
                            .clip(RoundedCornerShape(12.dp)),
                        contentScale = ContentScale.Crop
                    )
                }

                // Breadcrumb path
                Text(
                    text = "Konum: $breadcrumbPath",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Medium
                )

                // Category & Unit
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(10.dp)
                            .clip(CircleShape)
                            .background(categoryColor)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "Kategori: ${item.category}",
                        style = MaterialTheme.typography.bodyMedium
                    )
                }

                Text(
                    text = "Miktar: ${item.qty} ${item.unit}" + (if (item.qtyMin > 0) " (Min. Stok: ${item.qtyMin})" else ""),
                    style = MaterialTheme.typography.bodyMedium
                )

                if (item.price > 0) {
                    Text(
                        text = "Değer / Fiyat: ${item.price} ₺",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.primary
                    )
                }

                if (item.expiry.isNotBlank()) {
                    Text(text = "Son Kul. / Garanti: ${item.expiry}", style = MaterialTheme.typography.bodyMedium)
                }

                if (item.loanedTo.isNotBlank()) {
                    Text(text = "Ödünç Verildi: ${item.loanedTo}", style = MaterialTheme.typography.bodyMedium)
                }

                if (item.moveNo > 0) {
                    Text(text = "Taşınma Koli No: #${item.moveNo}", style = MaterialTheme.typography.bodyMedium)
                }

                if (item.tags.isNotBlank()) {
                    Text(text = "Etiketler: ${item.tags}", style = MaterialTheme.typography.bodySmall)
                }

                if (item.note.isNotBlank()) {
                    Text(text = "Not: ${item.note}", style = MaterialTheme.typography.bodyMedium)
                }
            }
        },
        confirmButton = {
            Button(onClick = {
                onDismiss()
                onEdit()
            }) {
                Text("Düzenle")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Kapat")
            }
        }
    )
}

@Composable
fun MoveItemDialog(
    rooms: List<RoomEntity>,
    onDismiss: () -> Unit,
    onSelectRoom: (targetRoomId: Long) -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = "Hangi Odaya Taşınsın?",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
        },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                rooms.forEach { room ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onSelectRoom(room.id) },
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                        )
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            val rt = EvimConstants.getRoomType(room.roomType)
                            Box(
                                modifier = Modifier
                                    .size(32.dp)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(rt.color),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(
                                    text = rt.abbr,
                                    color = Color.White,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                            Spacer(modifier = Modifier.width(12.dp))
                            Text(
                                text = room.name,
                                style = MaterialTheme.typography.bodyLarge,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("İptal")
            }
        }
    )
}

@Composable
fun ThemeDialog(
    currentTheme: EvimThemeMode,
    onDismiss: () -> Unit,
    onSelect: (EvimThemeMode) -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = "Tema Seçimi",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
        },
        text = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                EvimThemeMode.entries.forEach { mode ->
                    val isSelected = mode == currentTheme
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .clickable { onSelect(mode) }
                            .background(
                                if (isSelected) mode.primaryColor.copy(alpha = 0.15f)
                                else Color.Transparent
                            )
                            .padding(horizontal = 12.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(24.dp)
                                .clip(CircleShape)
                                .background(mode.primaryColor)
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Text(
                            text = mode.title,
                            style = MaterialTheme.typography.bodyLarge,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                            modifier = Modifier.weight(1f)
                        )
                        if (isSelected) {
                            Icon(
                                imageVector = Icons.Default.Check,
                                contentDescription = null,
                                tint = mode.primaryColor
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Tamam")
            }
        }
    )
}

@Composable
fun ConfirmDeleteDialog(
    title: String,
    message: String,
    onDismiss: () -> Unit,
    onConfirm: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(text = title, fontWeight = FontWeight.Bold)
        },
        text = {
            Text(text = message)
        },
        confirmButton = {
            Button(
                onClick = onConfirm,
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
            ) {
                Text("Sil")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("İptal")
            }
        }
    )
}
