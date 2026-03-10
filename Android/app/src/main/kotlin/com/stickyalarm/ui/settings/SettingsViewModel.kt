package com.stickyalarm.ui.settings

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.stickyalarm.data.ConfigRepository
import com.stickyalarm.data.model.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    application: Application,
    private val configRepository: ConfigRepository
) : AndroidViewModel(application) {

    private val _config = MutableStateFlow(Config())
    val config: StateFlow<Config> = _config.asStateFlow()

    private val _saveSuccess = MutableSharedFlow<Boolean>()
    val saveSuccess: SharedFlow<Boolean> = _saveSuccess.asSharedFlow()

    init {
        viewModelScope.launch {
            configRepository.configFlow.collect { loaded ->
                _config.value = loaded
            }
        }
    }

    fun updateConfig(transform: (Config) -> Config) {
        _config.value = transform(_config.value)
    }

    fun save() {
        viewModelScope.launch {
            configRepository.save(_config.value)
            _saveSuccess.emit(true)
        }
    }

    // Profile operations
    fun addProfile() {
        updateConfig { config ->
            val number = config.scheduleProfiles.size + 1
            config.copy(
                scheduleProfiles = config.scheduleProfiles + ScheduleProfile(name = "Profil $number")
            )
        }
    }

    fun removeProfile(profileId: String) {
        updateConfig { config ->
            if (config.scheduleProfiles.size <= 1) return@updateConfig config
            config.copy(
                scheduleProfiles = config.scheduleProfiles.filter { it.id != profileId },
                triggers = config.triggers.filter { it.profileId != profileId }
            )
        }
    }

    fun updateProfile(profileId: String, transform: (ScheduleProfile) -> ScheduleProfile) {
        updateConfig { config ->
            config.copy(
                scheduleProfiles = config.scheduleProfiles.map {
                    if (it.id == profileId) transform(it) else it
                }
            )
        }
    }

    // Trigger operations
    fun addTrigger(profileId: String, packageName: String) {
        updateConfig { config ->
            config.copy(
                triggers = config.triggers + TriggerEntry(
                    name = packageName,
                    type = "app",
                    profileId = profileId
                )
            )
        }
    }

    fun removeTrigger(triggerName: String, profileId: String) {
        updateConfig { config ->
            config.copy(
                triggers = config.triggers.filter {
                    !(it.name == triggerName && it.profileId == profileId)
                }
            )
        }
    }

    fun updateTriggerTimeLimit(triggerName: String, profileId: String, minutes: Int) {
        updateConfig { config ->
            config.copy(
                triggers = config.triggers.map {
                    if (it.name == triggerName && it.profileId == profileId) {
                        it.copy(timeLimitMinutes = minutes)
                    } else it
                }
            )
        }
    }

    // Launch apps
    fun addLaunchApp(profileId: String, packageName: String) {
        updateProfile(profileId) { profile ->
            profile.copy(launchApps = profile.launchApps + packageName)
        }
    }

    fun removeLaunchApp(profileId: String, packageName: String) {
        updateProfile(profileId) { profile ->
            profile.copy(launchApps = profile.launchApps.filter { it != packageName })
        }
    }
}
