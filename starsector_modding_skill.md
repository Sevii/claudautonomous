---
name: starsector-modding
description: Practical guide to modding Starsector (Fractal Softworks). Use when building or editing a Starsector mod — especially when defining custom star systems and planets, wiring up markets/conditions, or spawning special/boss enemy fleets via the campaign API, MagicLib, or MagicBounty.
---

# Starsector Modding — Skill Guide

Starsector mods are a mix of **data files** (a lenient JSON dialect + CSV tables) and **Java code** compiled against the game's API. This guide focuses on three tasks: creating **star systems**, creating **planets** (with markets), and spawning **special/boss enemy fleets**.

Reference points:
- Bundled API source: `starsector-core/` ships `starfarer.api.zip` (the public `com.fs.starfarer.api.*` source). Read it — it is the real documentation.
- Modding wiki: <https://starsector.fandom.com/wiki/Modding> and the official forum modding section.
- MagicLib (community utility library, near-universal dependency for fleet/bounty work): <https://github.com/MagicLibStarsector/MagicLib>

> **Version sensitivity.** Method signatures (`initStar`, `addPlanet`, fleet params) change between game releases (e.g. `0.96a` → `0.97a` → `0.98a`). Always confirm the exact signature against the `starfarer.api` source that ships with the game version you target. Examples below reflect the common modern API shape.

---

## 1. Mental model (read this first)

| Concept | Meaning |
|---|---|
| **Mod** | A folder under `Starsector/mods/<MyMod>/` containing at minimum `mod_info.json`. |
| **Data files** | JSON/CSV under `data/`. Loaded and merged with vanilla; CSVs are *row-merged* by id. |
| **Lenient JSON** | The parser allows `//` and `/* */` comments and trailing commas. It is **not** strict JSON. |
| **API jar** | `starfarer.api.jar` — you compile against it; never ship it. The campaign `impl` package is included as readable source and is the best example code you have. |
| **ModPlugin** | Your Java entry point (`extends BaseModPlugin`), declared in `mod_info.json`. Lifecycle hooks fire here. |
| **Sector / StarSystem / Market** | The campaign layer: `SectorAPI` holds `StarSystemAPI`s; planets/stations carry a `MarketAPI` (economy + conditions). |
| **CampaignFleetAPI** | A fleet on the campaign map. Built from `FleetMemberAPI`s (ships) with an optional commander `PersonAPI`. |

If you have modded other games: data files are like config, but most *behavior* (systems, fleets, missions) is created in code at new-game time or by always-running scripts.

---

## 2. Mod anatomy

```
mods/MyMod/
  mod_info.json
  data/
    config/                 # settings.json overrides, planets.json patches, custom config
    world/
      factions/             # *.faction files + factions.csv
    campaign/               # econ/condition CSVs, procgen tweaks
    hulls/, variants/       # ship definitions (if adding ships)
  jars/MyMod.jar            # your compiled code
  src/                      # your Java sources (not loaded at runtime)
  graphics/                 # textures (planets, stars, ships, icons)
  sounds/
```

### 2.1 `mod_info.json`

```json
{
  "id": "mymod",
  "name": "My Mod",
  "author": "you",
  "version": "1.0.0",
  "gameVersion": "0.97a-RC11",
  "jars": ["jars/MyMod.jar"],
  "modPlugin": "data.scripts.MyModPlugin",
  "dependencies": [
    { "id": "lw_lazylib", "name": "LazyLib" },
    { "id": "MagicLib", "name": "MagicLib" }
  ],
  "description": "Adds the Crimson Expanse and its warlords."
}
```

- `id` must be globally unique and is used everywhere as the namespace prefix for your data ids.
- `gameVersion` must match the target build or the launcher flags the mod.
- `jars` / `modPlugin` are omitted for pure data mods.

### 2.2 ModPlugin lifecycle

```java
package data.scripts;

import com.fs.starfarer.api.BaseModPlugin;
import com.fs.starfarer.api.Global;

public class MyModPlugin extends BaseModPlugin {
    @Override
    public void onApplicationLoad() { /* before any game; load configs */ }

    @Override
    public void onNewGame() { /* once, when a new save is created */ }

    @Override
    public void onNewGameAfterProcGen() {
        // Procedural sector exists but isn't finalized — THE place to add custom systems.
        new MyStarSystemGen().generate(Global.getSector());
    }

    @Override
    public void onGameLoad(boolean newGame) { /* every load; (re)install EveryFrameScripts */ }
}
```

Key timing for system generation: `onNewGameAfterProcGen()` (or `onNewGameAfterEconomyLoad()` if your markets must register after the economy is built). Adding systems on `onGameLoad` would duplicate them on every load — don't.

---

## 3. Tooling & workflow

- **Console Commands mod** is essential for testing. In-game: `runcode <java>`, `addship`, `spawnfleet`, `addmarketcondition`, `setrelation`, `god`, `nextwaystation`. `runcode` lets you exercise API snippets without recompiling.
- **Validate lenient JSON** before launching — a stray comma silently breaks loading; the `starsector.log` will name the file and line.
- **`starsector.log`** (in the game install dir) is your primary debugger. Most mod failures surface there as a `JSONException` or `NoSuchMethodError` (version mismatch).
- **Read the impl source.** Decompiled/bundled classes under `com.fs.starfarer.api.impl.campaign.procgen` (system generation) and `...fleet.FleetFactoryV3` are working reference implementations.
- **Compile** against `starfarer.api.jar` + any library jars (LazyLib, MagicLib). Target the Java version the game ships (historically Java 7/8 bytecode for older builds).

---

## 4. Creating a star system

A star system is created in code, typically a `generate(SectorAPI)` method called from `onNewGameAfterProcGen()`. Full annotated example:

```java
package data.scripts.world;

import com.fs.starfarer.api.Global;
import com.fs.starfarer.api.SectorAPI;
import com.fs.starfarer.api.campaign.*;
import com.fs.starfarer.api.impl.campaign.ids.*;
import java.awt.Color;

public class MyStarSystemGen {

    public void generate(SectorAPI sector) {
        StarSystemAPI system = sector.createStarSystem("Crimson Expanse");
        system.setBaseName("Crimson Expanse");

        // --- The star (orbit focus for everything) ---
        PlanetAPI star = system.initStar(
            "crimson",            // unique id (prefix with your mod for safety)
            StarTypes.ORANGE,     // star type, see planets.json "star_*" categories
            650f,                 // radius (pixels)
            200f);                // corona size
        system.setLightColor(new Color(255, 200, 150)); // ambient tint for the system

        // --- A habitable planet ---
        PlanetAPI planet = system.addPlanet(
            "crimson_prime",      // id
            star,                 // orbit focus
            "Crimson Prime",      // display name
            "terran",             // planet type id from planets.json
            45f,                  // starting orbit angle (degrees)
            150f,                 // planet radius
            2500f,                // orbit radius (distance from focus)
            120f);                // orbit period (days)
        planet.setCustomDescriptionId("planet_crimson_prime"); // optional, in descriptions.csv

        // --- A barren world farther out ---
        PlanetAPI rock = system.addPlanet("crimson_b", star, "Tartarus",
            "barren", 200f, 90f, 5000f, 200f);

        // --- Belts, rings, and terrain ---
        system.addAsteroidBelt(star, 300, 4000f, 256f, 120f, 180f);     // focus,count,orbitR,width,minDays,maxDays
        system.addRingBand(star, "misc", "rings_dust0", 256f, 0, Color.white,
            256f, 4000f, 150f);                                          // visual band over the belt

        // --- Jump point so the system is reachable ---
        JumpPointAPI jumpPoint = Global.getFactory().createJumpPoint("crimson_jump", "Crimson Jump-point");
        OrbitAPI orbit = Global.getFactory().createCircularOrbit(star, 90f, 3500f, 100f);
        jumpPoint.setOrbit(orbit);
        jumpPoint.setStandardWormholeToHyperspaceVisual();
        system.addEntity(jumpPoint);

        // --- Place in hyperspace + auto-create the matching hyperspace jump points ---
        system.setLocation(15000f, -8000f);            // hyperspace coordinates
        system.autogenerateHyperspaceJumpPoints(true, true);
    }
}
```

Key points:
- **`initStar` is mandatory and first** — it defines the system center and gravity well. For binary/trinary systems, add a second star as a `addPlanet(..., StarTypes.RED_DWARF, ...)` orbiting the primary, or use `system.setSecondary(...)` helpers in newer builds.
- **Orbits**: every entity needs an orbit or fixed location. Common setters on a `SectorEntityToken`: `setCircularOrbit(focus, angle, radius, days)`, `setCircularOrbitPointingDown(...)`, `setCircularOrbitWithSpin(...)`.
- **Reachability**: a system is only usable if it has a jump point and you call `autogenerateHyperspaceJumpPoints`. Forgetting `setLocation` puts it at hyperspace origin (overlapping the core).
- **Stations / gates**: `system.addCustomEntity("id", "Name", "station_side06", Factions.INDEPENDENT)` then give it an orbit. `"inactive_gate"` for a gate.

### 4.1 Adding to existing/procedural systems

To inject content into the procgenerated sector instead of a hand-built system, iterate `sector.getStarSystems()` and add entities, or implement a `ThemeGenerator`/`SectorGeneratorPlugin`-style class and run it from `onNewGameAfterProcGen()`. For "place N of these across random constellations," the procgen `themes` impl classes are the pattern to copy.

---

## 5. Creating planets (types, conditions, markets)

### 5.1 Planet & star types — `data/config/planets.json`

Planet/star *types* (texture, gravity, default conditions, glow) live in `planets.json`. To add a new type, merge an entry under `"planets"`:

```json
{
  "planets": {
    "my_crystal_world": {
      "name": "Crystalline World",
      "type": "planet",
      "texture": { "cat": "graphics/planets", "key": "my_crystal" },
      "icon": "my_crystal_icon",
      "rotation": 6,
      "starModType": "",
      "gravity": 0.6,
      "conditions": ["habitable", "ore_moderate"]
    }
  }
}
```

The `typeId` you pass to `addPlanet` (`"terran"`, `"barren"`, your `"my_crystal_world"`) must exist here. Star types referenced by `initStar` (`StarTypes.ORANGE`, etc.) are also defined in this file under their categories.

### 5.2 Market conditions

Conditions (gravity, atmosphere, hazards, resources) are defined in `data/campaign/market_conditions.csv` (+ generation tuning in `condition_gen_data.csv`). Use vanilla ids via the `Conditions` constants, e.g. `Conditions.HABITABLE`, `Conditions.ORE_RICH`, `Conditions.HOT`, `Conditions.LOW_GRAVITY`, `Conditions.RUINS_SCATTERED`.

### 5.3 Giving a planet a market (economy + population)

A planet with people, defenses, and trade needs a `MarketAPI`:

```java
import com.fs.starfarer.api.campaign.econ.MarketAPI;
import com.fs.starfarer.api.impl.campaign.ids.*;

MarketAPI market = Global.getFactory().createMarket("crimson_prime_market", "Crimson Prime", 5);
market.setFactionId(Factions.INDEPENDENT);
market.setPrimaryEntity(planet);
market.getConnectedEntities().add(planet);

// Population/size and key conditions
market.addCondition(Conditions.POPULATION_5);
market.addCondition(Conditions.HABITABLE);
market.addCondition(Conditions.MILD_CLIMATE);
market.addCondition(Conditions.ORE_MODERATE);

// Industries (jobs/economy)
market.addIndustry(Industries.POPULATION);
market.addIndustry(Industries.SPACEPORT);
market.addIndustry(Industries.MILITARYBASE);
market.addIndustry(Industries.MINING);

market.setSurveyLevel(MarketAPI.SurveyLevel.FULL);
market.setSize(5);
market.getTariff().modifyFlat("default_tariff", market.getFaction().getTariffFraction());

// Wire it up
planet.setMarket(market);
market.setPrimaryEntity(planet);
Global.getSector().getEconomy().addMarket(market, true); // true = with junk/initial stockpiles
```

Notes:
- Do market creation after the economy exists. If adding during sector gen, `onNewGameAfterEconomyLoad()` is the safe hook; otherwise the market may not register correctly.
- For an **uninhabited but conditioned** world (so survey/resources show without a population), create the market and call `market.setPlanetConditionMarketOnly(true)` and **don't** add `POPULATION`/`SPACEPORT`.
- Add stations/orbital stations as industries (`Industries.ORBITALSTATION`, `Industries.STARFORTRESS`) — these spawn defense fleets automatically.

---

## 6. Special / boss enemy fleets

There are three escalating approaches. Use the highest-level one that fits.

### 6.1 Build a fleet from scratch — `FleetFactoryV3`

For a hand-curated boss fleet (specific flagship + escorts), build an empty fleet and add members:

```java
import com.fs.starfarer.api.campaign.*;
import com.fs.starfarer.api.fleet.*;
import com.fs.starfarer.api.impl.campaign.fleets.FleetFactoryV3;
import com.fs.starfarer.api.impl.campaign.ids.*;

CampaignFleetAPI fleet = FleetFactoryV3.createEmptyFleet(
    Factions.PIRATES, FleetTypes.PATROL_LARGE, null);

// Add specific ship variants (ids from data/variants or your mod). Flagship first.
fleet.getFleetData().addFleetMember("onslaught_xiv_Elite");
fleet.getFleetData().addFleetMember("hammerhead_Elite");
fleet.getFleetData().addFleetMember("hammerhead_Elite");
fleet.getFleetData().addFleetMember("lasher_CS");
fleet.getFleetData().addFleetMember("lasher_CS");

fleet.setName("The Crimson Reaver");
fleet.setNoFactionInName(true);
fleet.getFleetData().setSyncNeeded();
fleet.forceSync();

// Flagship + commander
FleetMemberAPI flagship = fleet.getFleetData().getMembersListCopy().get(0);
fleet.getFleetData().setFlagship(flagship);

PersonAPI captain = OfficerManagerEvent.createOfficer(
    Global.getSector().getFaction(Factions.PIRATES), 10, true);
captain.setPersonality(Personalities.AGGRESSIVE);
captain.getName().setFirst("Mara");
captain.getName().setLast("Vance");
flagship.setCaptain(captain);
fleet.setCommander(captain);

// Place it in a system and give orders
StarSystemAPI system = Global.getSector().getStarSystem("Crimson Expanse");
system.addEntity(fleet);
fleet.setLocation(0, 0); // relative to system center; or near an entity
fleet.addAssignment(FleetAssignment.ORBIT_AGGRESSIVE,
    system.getEntityById("crimson_prime"), 1_000_000f);
```

### 6.2 Generate a balanced fleet by points — `FleetParamsV3`

When you want a faction-appropriate fleet auto-composed to a budget rather than a fixed list:

```java
FleetParamsV3 params = new FleetParamsV3(
    null,                       // source market (null = ad hoc)
    new Vector2f(0, 0),         // location hint
    Factions.PIRATES,           // faction
    2.0f,                       // quality override (ship/d-mod quality; null = faction default)
    FleetTypes.PATROL_LARGE,    // fleet type (affects naming/behavior)
    300f,                       // combatPts  (size of the combat portion)
    0f,                         // freighterPts
    0f,                         // tankerPts
    0f,                         // transportPts
    0f,                         // linerPts
    0f,                         // utilityPts
    0.5f);                      // qualityMod (extra quality bonus)
CampaignFleetAPI fleet = FleetFactoryV3.createFleet(params);
```

Higher `combatPts` → bigger fleet; `quality`/`qualityMod` → fewer d-mods and better variants. The composition is drawn from the faction's `.faction` file (its known ships and doctrine).

### 6.3 Make a fleet behave like a boss — memory flags & behavior

A fleet is just hostile-by-faction by default. To make it a relentless, non-ignorable boss:

```java
import com.fs.starfarer.api.impl.campaign.ids.MemFlags;

MemoryAPI mem = fleet.getMemoryWithoutUpdate();
mem.set(MemFlags.MEMORY_KEY_MAKE_HOSTILE, true);        // hostile regardless of reputation
mem.set(MemFlags.MEMORY_KEY_MAKE_AGGRESSIVE, true);     // engages instead of avoiding
mem.set(MemFlags.MEMORY_KEY_PURSUE_PLAYER, true);       // chases the player
mem.set(MemFlags.FLEET_DO_NOT_IGNORE_PLAYER, true);
mem.set(MemFlags.MEMORY_KEY_LOW_REP_IMPACT, true);      // killing it won't tank your rep
mem.set(MemFlags.MEMORY_KEY_NO_REP_IMPACT, true);

fleet.setTransponderOn(false);
fleet.getDetectedRangeMod().modifyFlat("boss", 5000f);  // visible from far away
```

To force-recover a unique flagship after the player wins, set the flagship variant as recoverable via the post-battle hook or use MagicLib/MagicBounty (below), which handles recovery declaratively.

### 6.4 MagicLib — `MagicCampaign.createFleet` (recommended for custom spawns)

MagicLib wraps all of the above into one call and is the de-facto standard:

```java
import org.magiclib.util.MagicCampaign;

CampaignFleetAPI fleet = MagicCampaign.createFleet(
    "The Crimson Reaver",            // fleet name
    FleetTypes.PATROL_LARGE,         // type
    Factions.PIRATES,                // faction
    "onslaught_xiv_Elite",           // flagship variant id
    true,                            // flagship is recoverable
    "The Reaver",                    // flagship name
    null,                            // captain (null = generated)
    /* preset variants */ presetMap, // Map<String,Integer> variantId -> count
    300f,                            // min fleet DP (auto-fills to budget)
    Factions.PIRATES,                // composition faction for the autofill
    2.0f,                            // quality
    null, null,                      // names, etc. (see signature)
    /* spawn location */ spawnLocation,
    FleetAssignment.PATROL_SYSTEM);  // initial assignment

MagicCampaign.spawnFleet(fleet, spawnLocation, ...);
```

Check the exact `createFleet`/`MagicFleetBuilder` signature in the MagicLib version you depend on — MagicLib favors a builder (`new MagicFleetBuilder()...`) in recent releases.

### 6.5 MagicBounty — declarative boss fleets with rewards (no Java)

For "a named warlord with a custom fleet, a deadline, a reward, and bar/intel hooks," MagicBounty (part of MagicLib) is data-only. Drop a file like `data/config/modFiles/magicBounty_data.json`:

```json
{
  "crimson_reaver_bounty": {
    "job_name": "The Crimson Reaver",
    "job_description": "Mara Vance has carved a fiefdom from the Crimson Expanse...",
    "job_forFaction": "independent",
    "job_deadline": 0,
    "job_credit_reward": 250000,
    "job_reward_scaling": false,

    "trigger_marketFaction_any": ["independent", "tritachyon"],
    "trigger_player_minLevel": 6,
    "trigger_min_days_elapsed": 30,
    "trigger_weight_mult": 1.0,

    "fleet_name": "Reaver's Wrath",
    "fleet_faction": "pirates",
    "fleet_flagship_variant": "onslaught_xiv_Elite",
    "fleet_flagship_name": "The Reaver",
    "fleet_flagship_recoverable": true,
    "fleet_flagship_alwaysRecoverable": false,
    "fleet_preset_ships": {
      "hammerhead_Elite": 2,
      "lasher_CS": 4
    },
    "fleet_scaling_multiplier": 1.5,
    "fleet_composition_faction": "pirates",
    "fleet_composition_quality": 2.0,
    "fleet_behavior": "AGGRESSIVE",
    "fleet_transponder": false,

    "fleet_spawnLocation": "IN_HYPERSPACE",
    "location_distance": "ANYWHERE",

    "job_show_distance": "VAGUE",
    "job_show_arrow": false
  }
}
```

Register the file in your `mod_info.json`/`MagicBounty` loader hook per MagicLib's docs. This gives you bar dialog, intel entry, deadline handling, scaled reward, and guaranteed flagship recovery for free — which is why most modern boss fleets ship as MagicBounties.

---

## 7. Spawning logic & timing

How fleets get into the world:

- **One-shot at new game**: spawn directly in `onNewGameAfterProcGen()` (e.g. a static boss guarding a system).
- **Recurring / conditional**: an `EveryFrameScript` (or `EveryFrameScriptWithCleanup`) installed in `onGameLoad`, which checks elapsed time / player level / location each frame and spawns when conditions are met. Remove finished scripts to avoid leaks.
- **Bar events / intel**: `BaseHubMission` / `HubMissionWithBarEvent` for player-initiated content; MagicBounty for the common boss-bounty case.
- **Faction patrols/raids**: handled by vanilla economy; tune via the faction file and market industries rather than spawning manually.

Always install `EveryFrameScript`s on `onGameLoad`, not `onNewGame`, so they exist after every load. Guard with a memory flag (`Global.getSector().getMemoryWithoutUpdate()`) so a one-time spawn doesn't repeat.

---

## 8. Quick reference card

| Task | API |
|---|---|
| Create system | `sector.createStarSystem("Name")` |
| Add star | `system.initStar(id, StarTypes.X, radius, corona)` |
| Add planet | `system.addPlanet(id, focus, name, typeId, angle, radius, orbitR, days)` |
| Asteroid belt | `system.addAsteroidBelt(focus, count, orbitR, width, minDays, maxDays)` |
| Ring band | `system.addRingBand(focus, cat, key, width, idx, color, ringW, orbitR, days)` |
| Jump point | `Global.getFactory().createJumpPoint(id, name)` + `system.addEntity` |
| Finalize system | `system.setLocation(x,y)` + `system.autogenerateHyperspaceJumpPoints(true,true)` |
| Custom entity/station | `system.addCustomEntity(id, name, "station_side06", faction)` |
| Create market | `Global.getFactory().createMarket(id, name, size)` |
| Register market | `Global.getSector().getEconomy().addMarket(market, true)` |
| Empty fleet | `FleetFactoryV3.createEmptyFleet(faction, type, null)` |
| Add ship | `fleet.getFleetData().addFleetMember("variant_id")` |
| Auto fleet | `FleetFactoryV3.createFleet(new FleetParamsV3(...))` |
| Officer | `OfficerManagerEvent.createOfficer(faction, level, true)` |
| Fleet orders | `fleet.addAssignment(FleetAssignment.X, target, durationDays)` |
| Boss flags | `fleet.getMemoryWithoutUpdate().set(MemFlags.MEMORY_KEY_MAKE_HOSTILE, true)` |
| MagicLib fleet | `MagicCampaign.createFleet(...)` / `MagicFleetBuilder` |
| Test in-game | Console Commands: `runcode`, `spawnfleet`, `addship` |

---

## 9. Gotchas

- **Lenient ≠ strict JSON.** Comments and trailing commas are allowed; a real syntax error names the file+line in `starsector.log`. Read the log first, always.
- **Wrong hook = duplicates or nulls.** Systems/markets on `onNewGameAfterProcGen` / `onNewGameAfterEconomyLoad`; scripts on `onGameLoad`. Never create world content on `onGameLoad`.
- **Forgetting `autogenerateHyperspaceJumpPoints`** leaves a system unreachable. Forgetting `setLocation` stacks it on the core.
- **`gameVersion` mismatch** disables the mod in the launcher; bump it for each game release and recheck signatures.
- **Don't ship `starfarer.api.jar`** or other game jars — compile against them only.
- **Unique ids.** Prefix every id (planets, markets, systems, fleets, conditions) with your mod id to avoid collisions with vanilla and other mods.
- **Faction file drives auto-composition.** `FleetParamsV3`/MagicLib autofill pull ships and doctrine from the `.faction` file — a fleet that "spawns wrong" is usually a faction-config issue, not a code one.
- **Boss recovery & rep.** Plain spawned fleets won't drop their unique flagship or protect your reputation; set memory flags or use MagicBounty, which handles both declaratively.
- **`forceSync()` after editing fleet contents** — skip it and the UI/stats can show stale data.
