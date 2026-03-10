package com.stickyalarm.ui.settings

import android.graphics.drawable.BitmapDrawable
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.graphics.drawable.toBitmap
import com.stickyalarm.ui.theme.*
import com.stickyalarm.util.getInstalledApps

@Composable
fun AppPickerDialog(
    excludePackages: Set<String> = emptySet(),
    onSelect: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    var searchQuery by remember { mutableStateOf("") }
    val allApps = remember {
        getInstalledApps(context)
            .filter { it.packageName !in excludePackages }
    }
    val filteredApps = remember(searchQuery, allApps) {
        if (searchQuery.isBlank()) allApps
        else {
            val q = searchQuery.lowercase()
            allApps.filter {
                it.label.lowercase().contains(q)
            }
        }
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = StickyCard,
        shape = RoundedCornerShape(18.dp),
        title = {
            Text("App auswählen", color = StickyText)
        },
        text = {
            Column(modifier = Modifier.fillMaxWidth()) {
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { searchQuery = it },
                    placeholder = { Text("Suchen...", color = StickyTextMuted) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = StickyText,
                        unfocusedTextColor = StickyText,
                        cursorColor = StickyAccent,
                        focusedBorderColor = StickyBorderFocus,
                        unfocusedBorderColor = StickyBorder
                    ),
                    shape = RoundedCornerShape(12.dp)
                )
                Spacer(modifier = Modifier.height(12.dp))
                LazyColumn(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 400.dp)
                ) {
                    items(filteredApps, key = { it.packageName }) { app ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { onSelect(app.packageName) }
                                .padding(vertical = 10.dp, horizontal = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            if (app.icon != null) {
                                val bitmap = remember(app.packageName) {
                                    app.icon.toBitmap(48, 48).asImageBitmap()
                                }
                                Image(
                                    bitmap = bitmap,
                                    contentDescription = app.label,
                                    modifier = Modifier.size(36.dp)
                                )
                                Spacer(modifier = Modifier.width(12.dp))
                            }
                            Text(
                                text = app.label,
                                style = MaterialTheme.typography.bodyLarge,
                                color = StickyText,
                                modifier = Modifier.weight(1f)
                            )
                        }
                        HorizontalDivider(color = StickySeparator)
                    }
                }
            }
        },
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Abbrechen", color = StickyTextMuted)
            }
        }
    )
}
