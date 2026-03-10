package com.stickyalarm.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.stickyalarm.data.model.Config
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import javax.inject.Inject
import javax.inject.Singleton

internal val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "sticky_alarm_config")
internal val CONFIG_KEY = stringPreferencesKey("config_json")

internal val json = Json {
    ignoreUnknownKeys = true
    encodeDefaults = true
    prettyPrint = true
}

@Singleton
class ConfigRepository @Inject constructor(
    @ApplicationContext private val context: Context
) {
    val configFlow: Flow<Config> = context.dataStore.data.map { preferences ->
        val jsonString = preferences[CONFIG_KEY]
        if (jsonString != null) {
            try {
                json.decodeFromString<Config>(jsonString)
            } catch (e: Exception) {
                Config()
            }
        } else {
            Config()
        }
    }

    suspend fun save(config: Config) {
        context.dataStore.edit { preferences ->
            preferences[CONFIG_KEY] = json.encodeToString(Config.serializer(), config)
        }
    }

    suspend fun load(): Config {
        return configFlow.first()
    }
}
