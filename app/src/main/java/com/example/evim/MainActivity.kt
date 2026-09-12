package com.example.evim

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.example.evim.ui.screens.HistoryScreen
import com.example.evim.ui.screens.HomeScreen
import com.example.evim.ui.screens.RoomScreen
import com.example.evim.ui.screens.SpecialListScreen
import com.example.evim.ui.theme.EvimAppTheme
import com.example.evim.ui.viewmodel.EvimViewModel

sealed interface ScreenState {
    data object Home : ScreenState
    data object Room : ScreenState
    data class Special(val listType: String, val title: String) : ScreenState
    data object History : ScreenState
}

class MainActivity : ComponentActivity() {
    private val viewModel: EvimViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            val currentTheme by viewModel.currentTheme.collectAsState()
            var currentScreen by remember { mutableStateOf<ScreenState>(ScreenState.Home) }

            EvimAppTheme(selectedTheme = currentTheme) {
                Surface(modifier = Modifier.fillMaxSize()) {
                    when (val screen = currentScreen) {
                        is ScreenState.Home -> {
                            HomeScreen(
                                viewModel = viewModel,
                                onNavigateToRoom = { room ->
                                    viewModel.enterRoom(room)
                                    currentScreen = ScreenState.Room
                                },
                                onNavigateToSpecial = { type, title ->
                                    currentScreen = ScreenState.Special(type, title)
                                },
                                onNavigateToHistory = {
                                    currentScreen = ScreenState.History
                                }
                            )
                        }

                        is ScreenState.Room -> {
                            BackHandler {
                                if (!viewModel.navigateUp()) {
                                    currentScreen = ScreenState.Home
                                }
                            }
                            RoomScreen(
                                viewModel = viewModel,
                                onNavigateBack = {
                                    if (!viewModel.navigateUp()) {
                                        currentScreen = ScreenState.Home
                                    }
                                }
                            )
                        }

                        is ScreenState.Special -> {
                            BackHandler {
                                currentScreen = ScreenState.Home
                            }
                            SpecialListScreen(
                                listType = screen.listType,
                                title = screen.title,
                                viewModel = viewModel,
                                onNavigateBack = {
                                    currentScreen = ScreenState.Home
                                }
                            )
                        }

                        is ScreenState.History -> {
                            BackHandler {
                                currentScreen = ScreenState.Home
                            }
                            HistoryScreen(
                                viewModel = viewModel,
                                onNavigateBack = {
                                    currentScreen = ScreenState.Home
                                }
                            )
                        }
                    }
                }
            }
        }
    }
}
