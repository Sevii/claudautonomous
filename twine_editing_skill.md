---
name: twine-editing
description: Practical guide for editing Twine 2 interactive fiction games using JavaScript, HTML, and CSS. Use when authoring or modifying a Twine story, choosing or customizing a story format (Harlowe, SugarCube, Snowman, Chapbook), styling passages, adding custom JS, or hand-editing a published Twine HTML file.
---

# Twine Editing — JS / HTML / CSS Skill Guide

Twine (https://twinery.org/) is an open-source tool for building branching, hypertext-based interactive fiction. A Twine project is a graph of **passages** authored in a chosen **story format**, which compiles down to a **single self-contained HTML file** that runs in any browser.

Sources:

- Adam Hammond's beginner Twine guide — <https://www.adamhammond.com/twineguide/>
- Twine 2 (the editor itself) — <https://github.com/klembot/twinejs>
- Snowman story format — <https://github.com/videlais/snowman> · <https://videlais.github.io/snowman/>
- SugarCube 2 docs — <https://www.motoslave.net/sugarcube/2/docs/>

---

## 1. Mental model (read this first)

| Concept | Meaning |
|---|---|
| **Passage** | A node of story text. Each passage has a name, body, and optional tags. The starting passage is the entry point. |
| **Story format** | The runtime engine compiled into the published HTML. Determines the macro syntax (`<<...>>`, `(...)`), state model, and JS API. **Choosing format is the most important decision** — guides for one format do not apply to another. |
| **Story JavaScript** | A special "script" passage executed once on story start. Use it to register macros, monkey-patch the engine, attach jQuery handlers. |
| **Story Stylesheet** | A special "stylesheet" passage whose contents become a `<style>` block in the published HTML. |
| **Passage tags** | Free-form labels. Every tag becomes a CSS class on the passage's `<tw-passage>`/element wrapper, so you can style passages by tag. |
| **Variables** | Persistent story state. Sigil and access pattern depend on format (`$x` in SugarCube/Harlowe; plain JS in Snowman). |
| **Story map** | The visual passage graph in the editor. Created via `Story → New` in twinery.org or the desktop build. |
| **Published HTML** | The single-file artifact (`File → Publish to File…`). Self-contained: includes engine, passages, JS, CSS. |

> **Pick the format before writing the game.** Switching later means rewriting every macro. Quick chooser:
>
> | If you want… | Use |
> |---|---|
> | The simplest, most-documented authoring experience | **Harlowe** (default) |
> | Save slots, complex variables, mature macro library, big community | **SugarCube 2** |
> | To write the game largely in JavaScript / jQuery, with full DOM control | **Snowman** |
> | A modern modifier-based, modular format with built-in CSS framework | **Chapbook** |

---

## 2. Where to put JS / HTML / CSS in the editor

Every Twine 2 story has two special passages alongside your normal ones. Open them from the story menu (the up-arrow next to the story title in twinery.org, or the **Story → Edit Story JavaScript / Edit Story Stylesheet** menu).

| Slot | Compiles to | What goes there |
|---|---|---|
| **Story JavaScript** | A `<script>` block executed once at startup | Macro definitions, jQuery handlers, helper functions, monkey-patches |
| **Story Stylesheet** | A `<style>` block in `<head>` | Global CSS, per-tag rules, font-faces |
| **Passage body** | An HTML/template fragment rendered when visited | The story text, choice links, inline macros, inline `<script>`/`<style>` (format permitting) |
| **Passage tag** | A class on the passage's wrapper element | Use for "haunted", "combat", "ending" etc. and target with `.haunted { background: black; color: red; }` |

Inside a passage body you can always use **raw HTML**: `<img src="images/key.png">`, `<div class="note">…</div>`, `<a href="https://…">link</a>`, etc. Relative paths work if you keep `images/`, `audio/`, etc. next to the published HTML.

---

## 3. CSS — works the same in every format

```css
/* Story Stylesheet */

body {
  background: #111;
  color: #eee;
  font-family: "Iowan Old Style", Georgia, serif;
  font-size: 1.1rem;
}

/* Per-tag styling: passages tagged "haunted" */
.haunted {
  background: #000;
  color: #c00;
  font-family: "Special Elite", monospace;
}

/* SugarCube: hide the left sidebar */
#ui-bar { display: none; }
#story  { margin-left: 0; }

/* Snowman / Harlowe links */
a, tw-link { color: #ffb454; text-decoration: none; }
a:hover, tw-link:hover { text-decoration: underline; }
```

Notes:

- The wrapper element name differs per format: SugarCube uses plain `div`/`a`; Harlowe uses custom `tw-*` elements (`tw-story`, `tw-passage`, `tw-link`, `tw-sidebar`). Inspect the rendered HTML with DevTools before writing selectors.
- Passage tags become classes; they're how you style "this scene only" without scoping selectors by hand.
- Web fonts: paste an `@font-face` (or a `@import url(...)` from Google Fonts) at the top of Story Stylesheet.

---

## 4. Format-specific cheat sheets

### 4.1 Harlowe (Twine 2 default)

Macros use **round brackets**, hooks use square brackets.

```harlowe
(set: $hasKey to false)
(set: $score to 0)

You see a rusty key on the floor.
[[Take it->KeyTaken]]

::KeyTaken
(set: $hasKey to true)
(set: $score to it + 1)
You pocket the key.
[[Continue->Door]]

::Door
{(if: $hasKey)[
  The key fits. The door swings open. [[Outside]]
](else:)[
  The door is locked. [[Search the room->Room]]
]}
```

- Variables are sigil'd: `$varname`. Use `(set:)`, `(if:)`, `(else-if:)`, `(else:)`, `(print: $x)`.
- Hooks: `[ ... ]` is a hook. `|name>[ ... ]` is a named hook you can target with `(replace: ?name)[…]`.
- Custom JS in Harlowe is **deliberately limited**. Use the Story JavaScript passage for jQuery DOM tweaks, but the macro language itself is the supported interface. To read state from JS: `Harlowe.API_ACCESS.STATE.variables` (subject to change between Harlowe versions; check your version's manual).
- CSS: target `tw-story`, `tw-passage`, `tw-link`, `tw-sidebar`, `tw-icon`.

### 4.2 SugarCube 2 (most common for non-trivial games)

Macros use **angle brackets**: `<<set>>`, `<<if>>`, `<<link>>`, `<<print>>`, `<<widget>>`, `<<script>>`.

```sugarcube
<<set $hasKey to false>>
<<set $score to 0>>

You see a rusty key on the floor.
[[Take it|KeyTaken]]

:: KeyTaken
<<set $hasKey to true>>
<<set $score += 1>>
You pocket the key.
[[Continue|Door]]

:: Door
<<if $hasKey>>
  The key fits. [[Outside]]
<<else>>
  The door is locked. [[Search|Room]]
<</if>>

<<textbox "$name" "" autofocus>>
<<button "Greet">>
  <<print "Hello, " + $name + "!">>
<</button>>
```

JavaScript API (from Story JavaScript or `<<script>>`):

```js
// Read & write story variables
State.variables.score += 1;
State.variables.flags = State.variables.flags || {};

// Temporary (per-turn) variables: prefix _ in passages, .temporary in JS
State.temporary.tmp = 42;

// Author namespace — survives passage navigation, NOT saved in history
setup.maxHP = 100;
setup.rollDie = (n = 6) => Math.floor(Math.random() * n) + 1;

// Custom macro
Macro.add("d6", {
  handler() {
    const r = setup.rollDie(6);
    $(this.output).wiki(String(r));   // .wiki() parses SugarCube markup
  },
});

// Listen for navigation
$(document).on(":passagedisplay", function (ev) {
  console.log("Now in passage:", ev.passage.title);
});
```

Key points:

- `$x` in passage = `State.variables.x` in JS. `_x` = `State.temporary.x`.
- **`State.variables` is saved/loaded** with the player's save. **`setup.*` is not** — put functions there, raw data in `State.variables`.
- Define reusable passage snippets with `<<widget "name">>…<</widget>>` in a passage tagged `widget`.
- Useful events on `$(document)`: `:passageinit`, `:passagestart`, `:passagedisplay`, `:passageend`. SugarCube ships with jQuery already loaded.
- Hide the left sidebar: `#ui-bar { display: none; }` plus `#story { margin-left: 4em; }`.

### 4.3 Snowman (write the game in JavaScript)

Snowman is "an advanced Twine 2 story format built for developers with JavaScript and CSS knowledge." It bundles **jQuery** and renders passages with **EJS-style template tags** instead of macros.

Install in twinery.org: **Story Formats → Add → JSONP URL** = `https://videlais.github.io/snowman/builds/2.X/format.js`.

Template tags inside a passage body:

| Tag | Behaviour |
|---|---|
| `<% js code %>` | Run JS, output nothing |
| `<%= expr %>` | Run JS, output result **escaped** for HTML safety |
| `<%- expr %>` | Run JS, output result **unescaped** (raw HTML) |

```html
<% s.score = (s.score || 0) + 1 %>
You enter a dark room. Score: <%= s.score %>

<% if (s.hasKey) { %>
  The door is unlocked. [[Outside]]
<% } else { %>
  The door is locked. [[Search the room->Room]]
<% } %>
```

JavaScript API (Snowman 2.x; expose globals: `window.story`, `window.passage`, and `s` as a shorthand for `story.state`):

```js
// In Story JavaScript
$(window).on('sm.passage.shown', function (_, data) {
  console.log('Showing', data.passage.name);
});

// Persistent story state — saved with the player's save
story.state.inventory = story.state.inventory || [];

// Jump to a passage by name
story.show('Outside');

// Render a named passage as HTML (without navigating)
const html = story.render('TooltipText');

// Find a passage by name
const p = story.passage('KeyTaken');
```

- `story.state` (alias `s` inside template tags) is the only thing **persisted to saves**. Anything you hang off `window` is not.
- Snowman passages use `[[Display Text->TargetPassage]]` for links. Plain `[[Target]]` also works.
- Because passages compile through a template engine, **untrusted text must use `<%= %>`** (escaped) — `<%- %>` is an XSS hole.
- Snowman gives you full DOM control via jQuery — write click handlers, animate scenes, swap audio. There's no macro layer to fight.

### 4.4 Chapbook (brief)

- Authoring style: front-matter "vars" section, then text, with `{insert}`-style modifiers.
- JavaScript API exposed as `engine.state.get('var')` / `engine.state.set('var', val)`.
- Use when you want a designed-for-prose format with a clean modifier system; less common than the three above.

---

## 5. Anatomy of a published Twine HTML file

`File → Publish to File…` in twinery.org produces one self-contained HTML. The structure (Twine 2):

```html
<html>
<head>
  <title>My Story</title>
  <style id="twine-user-stylesheet">/* your Story Stylesheet */</style>
  <!-- format engine CSS inline -->
</head>
<body>
  <tw-storydata
      name="My Story"
      startnode="1"
      creator="Twine"
      creator-version="2.x"
      format="SugarCube"
      format-version="2.x"
      ifid="UUID-HERE"
      options=""
      hidden>
    <style role="stylesheet" id="twine-user-stylesheet" type="text/twine-css">
      /* Story Stylesheet */
    </style>
    <script role="script" id="twine-user-script" type="text/twine-javascript">
      /* Story JavaScript */
    </script>
    <tw-passagedata pid="1" name="Start" tags="intro" position="100,100" size="100,100">
      Passage body text goes here.
      [[Continue->Next]]
    </tw-passagedata>
    <tw-passagedata pid="2" name="Next" ...>...</tw-passagedata>
  </tw-storydata>

  <!-- The story format engine (SugarCube/Harlowe/Snowman) is inlined here -->
  <script>/* engine source */</script>
</body>
</html>
```

Practical implications when **hand-editing or scripting** a published HTML:

1. **Passages live in `<tw-passagedata>` elements** under `<tw-storydata>`. The text is the element's text content; `name=""` is the passage name; `tags=""` is space-separated.
2. **Story JavaScript** is the `<script id="twine-user-script" type="text/twine-javascript">` block. It is **not executed by the browser directly** (the type isn't `application/javascript`); the engine reads it on startup.
3. **Story CSS** is the `<style id="twine-user-stylesheet" type="text/twine-css">` block. Same story — the engine injects it.
4. **The engine itself** is a plain `<script>` at the end of `<body>`. Replacing it changes story format (do not do this casually — passages may not parse against a different format).
5. **IFID** (`ifid` attribute) is the canonical interactive-fiction identifier; preserve it across edits.

To programmatically modify a published file, parse it with a DOM library (`jsdom` in Node, `BeautifulSoup` in Python) and edit `<tw-passagedata>` text content. Do **not** mangle the engine `<script>` block — its byte content matters.

Example (Node, jsdom):

```js
import { readFileSync, writeFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';

const dom = new JSDOM(readFileSync('story.html', 'utf8'));
const doc = dom.window.document;

for (const p of doc.querySelectorAll('tw-passagedata')) {
  const name = p.getAttribute('name');
  const text = p.textContent;
  if (name === 'Start') {
    p.textContent = text.replace(/rusty key/g, 'silver key');
  }
}

writeFileSync('story.patched.html', dom.serialize());
```

---

## 6. Twee — the text-format counterpart

Twine stories can also be authored as plain `.twee` text files (one passage per `:: Name [tags]` header). This is the format Tweego / Twine CLI tools eat. A passage looks like:

```twee
:: StoryTitle
My Game

:: StoryData
{
  "ifid": "00000000-0000-0000-0000-000000000000",
  "format": "SugarCube",
  "format-version": "2.36.1",
  "start": "Start"
}

:: Start [intro]
You wake up. [[Continue->Hallway]]

:: Hallway
A long corridor.
```

Use **Tweego** (<https://www.motoslave.net/tweego/>) to compile `.twee` → published HTML from the command line. This is the path of choice if you want to:

- Keep the story in git with diffs that make sense.
- Generate passages programmatically.
- Build the story in CI.

---

## 7. Common tasks — quick recipes

**Add a custom font:**

```css
/* Story Stylesheet */
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond&display=swap');
body { font-family: 'EB Garamond', Georgia, serif; }
```

**Hide the SugarCube sidebar entirely:**

```css
#ui-bar { display: none !important; }
#story  { margin-left: 2.5em; }
```

**Run code every time a passage is shown (SugarCube):**

```js
$(document).on(':passagedisplay', function (ev) {
  if (ev.passage.tags.includes('combat')) startCombatTimer();
});
```

**Run code every time a passage is shown (Snowman):**

```js
$(window).on('sm.passage.shown', function (_, data) {
  if (data.passage.tags.includes('combat')) startCombatTimer();
});
```

**Embed a video / audio clip from a relative folder:**

```html
<video src="media/intro.mp4" controls></video>
<audio src="audio/whisper.ogg" autoplay></audio>
```

When you publish, drop `media/` and `audio/` next to the HTML and ship the lot together (zip or static-host).

**Conditionally show a hook (Harlowe):**

```harlowe
(if: $hasKey)[The lock clicks open.](else:)[It won't budge.]
```

**Inject jQuery click handler inside a passage (Snowman/SugarCube):**

```html
<a id="open-door">Open door</a>
<script>
  $('#open-door').one('click', () => {
    State.variables.doorOpen = true;     // SugarCube
    // story.state.doorOpen = true;       // Snowman
    SugarCube.Engine.play('Outside');     // SugarCube nav
    // story.show('Outside');             // Snowman nav
  });
</script>
```

---

## 8. Gotchas

- **Don't mix format syntax.** A `<<set>>` macro in a Harlowe story does nothing. A `(set:)` in SugarCube prints literally. Pick one and stick to it.
- **Story JavaScript runs once.** Code that depends on a passage's DOM must run inside a passage event (`:passagedisplay`, `sm.passage.shown`) or inside an inline `<script>` in the passage body.
- **Save compatibility breaks** when you change the shape of `State.variables` mid-development. For released games, migrate old saves in a `:saveloaded` handler (SugarCube) instead of just renaming variables.
- **Snowman 1.x vs 2.x** APIs differ — `window.story`/`window.passage` and event names changed. Check the version you actually installed.
- **Don't paste secrets into a published HTML.** Everything in the file ships to the player, including your Story JavaScript.
- **`<%- %>` in Snowman is unescaped.** Never feed user input through it.
- **`format-version` matters.** A story authored against SugarCube 2.30 can break on SugarCube 2.36 if it relied on removed APIs. Pin the version in `StoryData`.
- **Backups.** Twine 2's web app stores stories in browser local storage. Use **Story → Publish to File…** or **Archive** regularly — clearing site data wipes everything.

---

## 9. Toolchain summary

| Tool | Use |
|---|---|
| **twinery.org** | Browser editor — fastest start. |
| **Twine 2 desktop** | Same editor, packaged with Electron. Saves to disk. |
| **Tweego** | CLI compiler: `.twee` + format → `.html`. Best for source-control and CI. |
| **Twine 2 CLI / extwee** | Node.js tooling for parsing/decompiling published HTML. |
| **DevTools** | Inspect the live story DOM; selectors and events behave like any web page. |
| **`jsdom` / `BeautifulSoup`** | Programmatic post-processing of a published file. |

Reach for **Tweego + a story format of your choice + your editor** as soon as the project outgrows the visual map; from that point on, editing a Twine game is just editing JS/HTML/CSS in plain files.
