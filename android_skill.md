---
name: android-development
description: Modern Android development best practices for 2026 using Kotlin, Jetpack Compose, and the recommended Google architecture. Use when building, refactoring, or reviewing native Android apps, or when answering questions about Android architecture, UI, data, testing, DI, navigation, or performance.
---

# Android Development (2026) — Kotlin + Jetpack Compose

Authoritative context for building production-quality Android apps in 2026. Favor the choices in this document unless the user explicitly asks otherwise; if a user's codebase predates these patterns, propose incremental migration instead of a big-bang rewrite.

## 1. Recommended Stack (Defaults)

| Concern | Default in 2026 |
|---|---|
| Language | Kotlin 2.2+ (K2 compiler) |
| UI | Jetpack Compose + Material 3 |
| Navigation | Navigation 3 (Nav3), type-safe with `@Serializable` routes |
| Architecture | MVVM with unidirectional data flow (MVI where state is complex) |
| State | `ViewModel` + `StateFlow` + immutable `UiState` data classes |
| DI | Hilt (Dagger under the hood), KSP — not kapt |
| Async | Coroutines + Flow; `viewModelScope` and `repositoryScope` |
| Local storage | Room (KMP-compatible) + Preferences/Proto DataStore |
| Networking | Retrofit + OkHttp for Android-only; Ktor Client for KMP |
| Images | Coil 3 (Compose-first, KMP) |
| Background | WorkManager for deferrable/guaranteed work |
| Build | Gradle with Kotlin DSL + Version Catalogs (`libs.versions.toml`) |
| Min SDK | 24 (Android 7.0) typical; target SDK = latest stable |
| Testing | JUnit 5, MockK, Turbine, Compose UI Test v2, Robolectric 4.x |
| Performance | R8 full mode + Baseline Profiles + Macrobenchmark |
| Cross-platform (optional) | Kotlin Multiplatform 2.x; Compose Multiplatform for shared UI |

## 2. Architecture

Google's recommended architecture is a three-layer split with a strict unidirectional data flow:

```
UI layer  →  Domain layer (optional)  →  Data layer
   ▲                                         │
   └─────────────── observes flows ──────────┘
```

- **UI layer**: `@Composable` screens + `ViewModel` that exposes a single `StateFlow<UiState>`.
- **Domain layer** (optional): stateless `UseCase`/`Interactor` classes — add only when orchestration logic is reused across ViewModels.
- **Data layer**: Repositories are the single source of truth. Repositories combine one or more `DataSource` classes (Room, Retrofit/Ktor, DataStore).

Rules of thumb:
- ViewModels must not depend on Android framework types (`Context`, `Resources`, etc.) directly. Pass strings/ids through the UI state and resolve in the composable.
- Repositories return `Flow<T>` or suspend functions; they never expose `LiveData` or Android types in new code.
- Keep `UiState` immutable. Mutations happen inside the ViewModel via `.update { it.copy(...) }` on a `MutableStateFlow`.

### MVVM vs MVI
- Start with **MVVM + UDF**: one `StateFlow<UiState>` out, suspend/intent functions in. This covers most screens.
- Graduate to **MVI** (explicit `Intent` + `Reducer`) only when a screen has many interleaved async operations and debugging state transitions matters. Using both in the same app is normal and fine.

## 3. UI with Jetpack Compose

- Use Compose for all new UI. Do not mix Views and Compose on the same screen unless migrating.
- Prefer **stateless composables**: accept state + callbacks, never read a ViewModel directly except at the screen root.
- Hoist state up to the level that needs to read or write it; no further.
- Material 3 (`androidx.compose.material3`) is the default design system. Use dynamic color on Android 12+ and provide a fallback scheme.
- Collect flows lifecycle-safely:

```kotlin
val uiState by viewModel.uiState.collectAsStateWithLifecycle()
```

Never use plain `.collectAsState()` for flows backed by work that should stop when the screen is not visible.

### Performance-sensitive Compose rules
- Pass **stable** types into composables. Annotate data classes with `@Immutable`/`@Stable` when Compose's inference cannot see stability (e.g., types from other modules).
- Use `key =` in `LazyColumn` / `LazyRow` `items`.
- Read state as late as possible. If only a Text reads `counter`, only that Text should recompose — push the read into a lambda (`Text(text = { counter.toString() })` pattern or a child composable).
- Defer reads with `derivedStateOf` for expensive computations.
- Avoid `Modifier.clickable {}` capturing unstable lambdas; prefer `remember`-ed callbacks or references to ViewModel methods.
- Use `@Preview` with multiple device configs, dark mode, and RTL; use `@PreviewParameter` for parameterized previews.

### Navigation 3 (Nav3)
Nav3 is stable and the AndroidX Compose-first navigation library. Routes are Kotlin types, not strings.

```kotlin
@Serializable data object Home : NavKey
@Serializable data class Details(val id: String) : NavKey

NavDisplay(
    backStack = backStack,
    entryProvider = entryProvider {
        entry<Home> { HomeScreen(onItem = { backStack.add(Details(it)) }) }
        entry<Details> { DetailsScreen(id = it.id, onBack = { backStack.removeLastOrNull() }) }
    },
)
```

- Store the back stack in the ViewModel or a navigator class to survive config changes.
- Use adaptive layouts (list-detail) with Nav3's built-in scene helpers for tablets / foldables.
- For legacy Nav2 codebases, migrate incrementally: swap route strings for type-safe `@Serializable` destinations first, then move to Nav3.

## 4. State Management Pattern

```kotlin
@HiltViewModel
class TaskListViewModel @Inject constructor(
    private val repo: TaskRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        repo.observeTasks()
            .onEach { tasks -> _uiState.update { it.copy(tasks = tasks, loading = false) } }
            .catch { e -> _uiState.update { it.copy(error = e.message, loading = false) } }
            .launchIn(viewModelScope)
    }

    fun onToggle(id: String) = viewModelScope.launch { repo.toggle(id) }

    data class UiState(
        val tasks: List<Task> = emptyList(),
        val loading: Boolean = true,
        val error: String? = null,
    )
}
```

- Use `stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), initial)` when deriving a `StateFlow` from cold flows, so upstream work stops during config changes but doesn't restart.
- One-time events (snackbars, navigation) belong in a `Channel<Event>` exposed as a `Flow`, not in the `UiState`. Compose cannot consume one-shot state values reliably.

## 5. Dependency Injection with Hilt

Setup (Gradle, KSP — not kapt):

```kotlin
// build.gradle.kts (module)
plugins {
    id("com.google.devtools.ksp")
    id("com.google.dagger.hilt.android")
}
dependencies {
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
}
```

Rules:
- `@HiltAndroidApp` on `Application`.
- `@AndroidEntryPoint` on Activities/Fragments/Services.
- `@HiltViewModel` + `@Inject` constructor on ViewModels.
- Prefer `@Binds` over `@Provides` when binding an interface to its implementation — it generates less code.
- Use `@Singleton` sparingly (true app-wide singletons: OkHttpClient, Room, DataStore). Use `@ViewModelScoped` for per-screen caches.
- Use qualifiers (`@Qualifier annotation class IoDispatcher`) to disambiguate `CoroutineDispatcher`s instead of string names.
- For tests, replace modules with `@TestInstallIn` and inject fakes.

## 6. Data Layer

### Offline-first by default
Treat the network as an enhancement, not a prerequisite. Every read goes to Room; every write updates Room immediately and enqueues a sync.

```kotlin
class TaskRepositoryImpl @Inject constructor(
    private val dao: TaskDao,
    private val api: TaskApi,
    private val workManager: WorkManager,
) : TaskRepository {
    override fun observeTasks(): Flow<List<Task>> = dao.observeAll().map { it.map(TaskEntity::toDomain) }

    override suspend fun toggle(id: String) {
        dao.toggle(id, pendingSync = true)
        workManager.enqueueUniqueWork(
            "sync-$id",
            ExistingWorkPolicy.REPLACE,
            OneTimeWorkRequestBuilder<SyncTaskWorker>()
                .setInputData(workDataOf("id" to id))
                .setConstraints(Constraints(requiredNetworkType = NetworkType.CONNECTED))
                .build(),
        )
    }
}
```

### Room
- Use Room 2.8+. Define `@Entity` classes separate from domain models; map in the repository.
- Expose `Flow<T>` queries for observation; `suspend` for one-shots.
- Enable `@AutoMigration` where possible; write `Migration` classes only when autogeneration can't infer intent.
- Turn on schema export and commit `schemas/` to version control.

### DataStore
- **Preferences DataStore** for small key/value config.
- **Proto DataStore** for typed, structured state — better than raw JSON.
- Never use SharedPreferences in new code.

### Networking
- **Retrofit + OkHttp + kotlinx.serialization** for Android-only apps.
- **Ktor Client** for KMP.
- Centralize error mapping in a single `NetworkResult<T>` / `Result<T>`-style wrapper — don't leak `HttpException` into ViewModels.
- Use OkHttp interceptors for auth, logging (debug only), and retry-with-backoff. Pair with a `TokenRefreshAuthenticator` for 401s.

## 7. Concurrency

- `Dispatchers.Main.immediate` for UI, `Dispatchers.IO` for blocking I/O, `Dispatchers.Default` for CPU work.
- Inject dispatchers — don't hardcode `Dispatchers.IO` inside suspend functions. It makes tests flaky.
- Use **structured concurrency**: every `launch` lives inside a scope with a known lifecycle (`viewModelScope`, `lifecycleScope`, a custom `CoroutineScope` in a singleton with `SupervisorJob`).
- Prefer `supervisorScope` when one child's failure should not cancel siblings.
- Use `Flow` combinators (`combine`, `flatMapLatest`, `debounce`) instead of manually managing subscriptions.

## 8. Testing

Compose testing was overhauled — **v2 test APIs are now the default** and use `StandardTestDispatcher`, so coroutines are queued until the virtual clock advances. Old `UnconfinedTestDispatcher`-style behavior is deprecated.

- **Unit tests**: JUnit 5, MockK, `kotlinx-coroutines-test` (`runTest`), **Turbine** for flows.
- **Compose UI tests**: `createComposeRule()` or `runComposeUiTest { }`. Advance the clock explicitly where needed.
- **Instrumented tests**: Robolectric 4 for most Android framework tests; keep real-device tests for things that touch GPU, camera, or OS integration.
- **Hilt tests**: `@HiltAndroidTest` + `@TestInstallIn` to swap fakes.
- **Screenshot tests**: Paparazzi (JVM, fast, no emulator) or Roborazzi (Compose-aware).

Example ViewModel test with Turbine:

```kotlin
@Test fun `toggles task`() = runTest {
    val repo = FakeTaskRepository(listOf(Task("1", done = false)))
    val vm = TaskListViewModel(repo)

    vm.uiState.test {
        assertEquals(false, awaitItem().tasks.first().done)
        vm.onToggle("1")
        assertEquals(true, awaitItem().tasks.first().done)
        cancelAndIgnoreRemainingEvents()
    }
}
```

## 9. Performance

The two highest-ROI changes are almost always free:

1. **Enable R8 full mode** (default in recent AGP). Verify `android.enableR8.fullMode=true` in `gradle.properties` and keep `minifyEnabled = true` on release.
2. **Ship a Baseline Profile** generated with Macrobenchmark. Ship-day gains of 20–50% on startup and scroll are normal (Reddit: 51% faster feed startup; Monzo: P90 scroll 71% faster).

Other wins:
- Use **Startup Profiles** alongside Baseline Profiles to optimize pre-main code paths.
- Measure with **Macrobenchmark** + **Jetpack JankStats** in production.
- Use **Cloud Profiles** (Play Store automatically collects them) as a complement, not a replacement.
- Defer work in `Application.onCreate()`; use `androidx.startup` + `WorkManager`.
- Kill Compose recompositions with the Layout Inspector's recomposition counter before optimizing guesses.

## 10. Modularization

For apps beyond ~50k LOC, split into Gradle modules:

```
:app
:core:designsystem    // theme, components
:core:data            // repositories, network, db
:core:domain          // use cases (if used)
:core:common          // utils, dispatchers, result types
:feature:home
:feature:details
:feature:settings
```

- Features depend on `:core:*`, never on other features.
- Use **convention plugins** in `build-logic/` to share Gradle config instead of copy-pasting.
- Use `libs.versions.toml` version catalog.
- Consider KSP + `isolated-projects` and configuration cache for build-time wins.

## 11. Kotlin Multiplatform (When to Use)

KMP is production-ready in 2026 — Netflix, McDonald's, Cash App ship it. Consider it when:
- You have an iOS counterpart app and shared business logic.
- Your team is comfortable maintaining Gradle + Xcode interop.

What to share:
- ✅ Data layer (Ktor, Room 2.8+, DataStore, SQLDelight)
- ✅ ViewModels (`androidx.lifecycle:lifecycle-viewmodel` is KMP)
- ✅ Use cases / domain
- ⚠️ UI via **Compose Multiplatform** — stable on Android, iOS, desktop; web is beta. Adopt when design parity matters more than platform-native feel.

Don't rewrite a working Android-only app to KMP unless you're also shipping iOS.

## 12. Security Baseline

- Use `EncryptedSharedPreferences` / Tink — or better, Proto DataStore + Android Keystore for secrets.
- Never ship API keys in source; use `local.properties` + BuildConfig, or (better) obtain tokens via backend.
- `usesCleartextTraffic = false`; define a Network Security Config.
- Add certificate pinning via OkHttp for sensitive endpoints.
- Request the minimum permissions, and use **runtime permissions** with the Accompanist/AndroidX permissions APIs.
- Set `android:allowBackup="false"` unless you intentionally support it, and scope backups with `fullBackupContent`.

## 13. Common Pitfalls

- `remember { viewModel() }` — **don't**. Use `hiltViewModel()` or `viewModel()` directly.
- Collecting flows with `collectAsState()` instead of `collectAsStateWithLifecycle()` — causes work in the background.
- Holding a `Context` in a ViewModel — leaks. Use `@ApplicationContext` injection only when truly needed.
- Putting one-shot events in `UiState` — Compose deduplicates equal values; the event will be missed. Use a `Channel`.
- `GlobalScope.launch { }` — unstructured. Use a scoped `CoroutineScope` with `SupervisorJob`.
- `runBlocking` in production code — almost always wrong.
- Passing unstable lambdas / non-`@Stable` types into composables — kills recomposition skipping.
- Skipping R8 / Baseline Profiles on release — leaves 20–50% performance on the table.
- Mixing kapt with KSP — slower builds. Move everything to KSP.
- Storing secrets in `BuildConfig` fields that ship in the APK — treat them as public.

## 14. Decision Quick-Reference

| Question | Default answer |
|---|---|
| XML or Compose? | Compose |
| Nav2 or Nav3? | Nav3 |
| LiveData or StateFlow? | StateFlow |
| kapt or KSP? | KSP |
| SharedPreferences or DataStore? | DataStore |
| Dagger manual or Hilt? | Hilt |
| MVVM or MVI? | MVVM; MVI for complex stateful screens |
| Retrofit or Ktor (Android only)? | Retrofit |
| Retrofit or Ktor (KMP)? | Ktor |
| GSON or kotlinx.serialization? | kotlinx.serialization |
| Glide/Picasso or Coil? | Coil 3 |
| Groovy or Kotlin DSL for Gradle? | Kotlin DSL + version catalog |

## 15. Starter Module Template (copy-ready)

```kotlin
// settings.gradle.kts
dependencyResolutionManagement {
    versionCatalogs { create("libs") { from(files("gradle/libs.versions.toml")) } }
}

// build.gradle.kts (feature module)
plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
    alias(libs.plugins.compose.compiler)
}
android {
    compileSdk = 35
    defaultConfig { minSdk = 24 }
    buildFeatures { compose = true }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.bundles.compose)
    implementation(libs.androidx.navigation3)
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
    implementation(libs.androidx.hilt.navigation.compose)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.kotlinx.serialization.json)

    testImplementation(libs.junit5)
    testImplementation(libs.mockk)
    testImplementation(libs.turbine)
    testImplementation(libs.kotlinx.coroutines.test)
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
}
```

---

**When in doubt**: check [d.android.com/topic/architecture](https://developer.android.com/topic/architecture) and the Now in Android sample (`android/nowinandroid` on GitHub) — both are maintained by Google's Android DevRel team and reflect the current recommendations.
