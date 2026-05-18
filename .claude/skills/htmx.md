# HTMX Skill

Use this skill when the user is building web applications with HTMX, asking about HTMX attributes/patterns, or wants to add HTMX interactivity to HTML pages.

## What is HTMX

HTMX extends HTML as a hypertext by allowing any element to issue HTTP requests triggered by any event, using any HTTP verb, with responses swapped into any target element — all from declarative attributes in HTML, without writing JavaScript.

**Installation:**
```html
<script src="https://unpkg.com/htmx.org@2.0.4"></script>
```

Or via npm: `npm install htmx.org`

## Core Attributes

### HTTP Request Attributes
| Attribute | Description |
|-----------|-------------|
| `hx-get` | Issues a GET request to the specified URL |
| `hx-post` | Issues a POST request to the specified URL |
| `hx-put` | Issues a PUT request to the specified URL |
| `hx-patch` | Issues a PATCH request to the specified URL |
| `hx-delete` | Issues a DELETE request to the specified URL |

### Trigger, Target, and Swap
| Attribute | Description |
|-----------|-------------|
| `hx-trigger` | Specifies the event that triggers the request |
| `hx-target` | CSS selector specifying the target element for the response swap |
| `hx-swap` | Controls how the response content is swapped in |
| `hx-select` | CSS selector to extract a subset of the response |

### Default Triggers
- `input`, `textarea`, `select` elements: `change` event
- `form` elements: `submit` event
- Everything else: `click` event

## hx-trigger Syntax

```
hx-trigger="event[filter] modifier1 modifier2, event2"
```

**Modifiers:**
- `once` — Only trigger once
- `changed` — Only trigger if element value changed
- `delay:<time>` — Wait before issuing request (e.g., `delay:500ms`). Resets on re-trigger (debounce).
- `throttle:<time>` — Throttle requests to at most once per interval
- `from:<CSS selector>` — Listen for event on a different element (supports `document`, `window`, `closest <selector>`, `find <selector>`, `next <selector>`, `previous <selector>`)
- `target:<CSS selector>` — Filter events to only those originating from matching elements
- `consume` — Prevent event propagation
- `queue:<strategy>` — Queue strategy: `first`, `last` (default), `all`, `none`

**Event Filters:**
Square bracket expressions evaluated against the event: `hx-trigger="click[ctrlKey]"`

**Special Events:**
- `load` — Fires on element load (good for lazy loading)
- `revealed` — Fires when element scrolls into viewport
- `intersect` — Fires when element intersects viewport (supports `root:<selector>` and `threshold:<float>`)
- `every <interval>` — Polling (e.g., `every 2s`). Add `[condition]` to stop: `every 2s [someVar]`

## hx-target Extended Selectors

- `this` — The element itself
- `closest <selector>` — Closest ancestor matching selector
- `find <selector>` — First child matching selector
- `next <selector>` — Next sibling matching selector (scans forward in DOM)
- `previous <selector>` — Previous sibling matching selector (scans backward in DOM)

## hx-swap Values

| Value | Description |
|-------|-------------|
| `innerHTML` | **(default)** Replace inner HTML of target |
| `outerHTML` | Replace the entire target element |
| `afterbegin` | Prepend before first child of target |
| `beforebegin` | Insert before the target element |
| `beforeend` | Append after last child of target |
| `afterend` | Insert after the target element |
| `delete` | Delete the target element |
| `none` | Do not swap, but still process response headers |

**Swap Modifiers** (appended to swap value):
```
hx-swap="innerHTML transition:true swap:500ms settle:500ms scroll:top show:top focus-scroll:true"
```
- `transition:true` — Use View Transition API
- `swap:<delay>` — Delay between removing old and inserting new content
- `settle:<delay>` — Delay between inserting new and settling attributes
- `ignoreTitle:true` — Ignore title tags in response
- `scroll:top` / `scroll:bottom` — Scroll target element
- `scroll:<selector>:top` — Scroll specific element
- `show:top` / `show:bottom` — Scroll element into viewport
- `show:window:top` — Scroll window to top
- `focus-scroll:true` / `focus-scroll:false` — Control autofocus scroll behavior

## Parameters and Values

| Attribute | Description |
|-----------|-------------|
| `hx-include` | CSS selector for additional elements whose values to include |
| `hx-params` | Filter parameters: `*` (all), `none`, `not <list>`, or `<param-list>` |
| `hx-vals` | Add static values (JSON): `hx-vals='{"key": "value"}'` |
| `hx-vals` | Add dynamic values (JS): `hx-vals="js:{key: computeValue()}"` |
| `hx-headers` | Add custom headers (JSON): `hx-headers='{"X-Custom": "value"}'` |
| `hx-encoding` | Set to `multipart/form-data` for file uploads |

## Request Control

| Attribute | Description |
|-----------|-------------|
| `hx-confirm` | Show `confirm()` dialog before request |
| `hx-prompt` | Show `prompt()` before request; value available as `HX-Prompt` header |
| `hx-disable` | Disable htmx processing on this element and children |
| `hx-disabled-elt` | CSS selector for elements to disable during request |
| `hx-indicator` | CSS selector for element to show during request |
| `hx-sync` | Synchronize requests between elements |
| `hx-validate` | Force HTML5 validation before request |
| `hx-request` | Configure request options: `timeout`, `credentials`, `noHeaders` |

### hx-sync Strategies
```html
<div hx-sync="closest form:abort">    <!-- Abort if form request in flight -->
<div hx-sync="closest form:drop">     <!-- Drop this request if form request in flight -->
<div hx-sync="closest form:replace">  <!-- Abort current, send this one -->
<div hx-sync="closest form:queue">    <!-- Queue behind current request -->
<div hx-sync="closest form:queue first">  <!-- Queue only first -->
<div hx-sync="closest form:queue last">   <!-- Queue only last -->
<div hx-sync="closest form:queue all">    <!-- Queue all -->
```

## Out of Band (OOB) Swaps

Server responses can update multiple parts of the page. Add `hx-swap-oob="true"` to response elements with matching IDs:

```html
<!-- Main response swaps into target normally -->
<div id="main-content">Updated content</div>

<!-- OOB elements swap into matching IDs anywhere in the DOM -->
<div id="notification" hx-swap-oob="true">New notification!</div>
<div id="sidebar" hx-swap-oob="outerHTML">Updated sidebar</div>
```

For elements that can't be direct children of certain containers (e.g., table rows), use `<template>`:
```html
<template><tr id="row-1" hx-swap-oob="true"><td>Updated</td></tr></template>
```

Select specific OOB elements from a response:
```html
<div hx-select-oob="#notification,#sidebar">
```

## Attribute Inheritance

Most `hx-*` attributes are inherited by child elements. This lets you set attributes at a parent level:

```html
<div hx-target="#result" hx-swap="outerHTML">
  <button hx-get="/item/1">Item 1</button>  <!-- Inherits target and swap -->
  <button hx-get="/item/2">Item 2</button>  <!-- Inherits target and swap -->
</div>
```

- Disable inheritance for a specific attribute: `hx-confirm="unset"`
- Disable inheritance per-element: `hx-disinherit="*"` or `hx-disinherit="hx-target hx-swap"`
- Force disable all inheritance globally: `htmx.config.disableInheritance = true`, then use `hx-inherit` to opt in

## Boosting

`hx-boost="true"` progressively enhances links and forms to use AJAX:

```html
<div hx-boost="true">
  <a href="/page">Link</a>           <!-- Becomes AJAX GET, swaps body -->
  <form action="/submit">...</form>   <!-- Becomes AJAX POST, swaps body -->
</div>
```

## History Support

| Attribute | Description |
|-----------|-------------|
| `hx-push-url` | Push URL to browser history (`true`, `false`, or custom URL) |
| `hx-replace-url` | Replace current URL in history (`true`, `false`, or custom URL) |
| `hx-history` | Set to `false` to prevent page from being cached in history |
| `hx-history-elt` | Element to snapshot for history (default: body) |

## CSS Classes and Indicators

**Automatic CSS classes applied by htmx:**
| Class | When Applied |
|-------|-------------|
| `htmx-added` | New content before swap, removed after settle |
| `htmx-indicator` | Toggled visible during `htmx-request` |
| `htmx-request` | Applied during active request |
| `htmx-settling` | Applied after swap, removed after settle |
| `htmx-swapping` | Applied before swap, removed after swap |

**Loading indicator pattern:**
```html
<button hx-get="/data" hx-indicator="#spinner">Load</button>
<span id="spinner" class="htmx-indicator">Loading...</span>
```

The `.htmx-indicator` class sets `opacity: 0` by default. When a request is in flight, `htmx-request` is added to the triggering element, and the indicator's opacity transitions to `1`.

## Request Headers (sent by htmx)

| Header | Value |
|--------|-------|
| `HX-Request` | Always `"true"` |
| `HX-Current-URL` | Current browser URL |
| `HX-Target` | ID of target element |
| `HX-Trigger` | ID of triggered element |
| `HX-Trigger-Name` | Name of triggered element |
| `HX-Boosted` | `"true"` if via `hx-boost` |
| `HX-Prompt` | User response to `hx-prompt` |
| `HX-History-Restore-Request` | `"true"` if restoring from history cache |

## Response Headers (sent by server)

| Header | Effect |
|--------|--------|
| `HX-Location` | Client-side redirect without full page reload (JSON: `{"path":"/new", "target":"#content"}`) |
| `HX-Push-Url` | Push URL into browser history |
| `HX-Replace-Url` | Replace URL in browser history |
| `HX-Redirect` | Full client-side redirect |
| `HX-Refresh` | `"true"` triggers full page refresh |
| `HX-Reswap` | Override `hx-swap` value |
| `HX-Retarget` | Override `hx-target` with CSS selector |
| `HX-Reselect` | Override `hx-select` with CSS selector |
| `HX-Trigger` | Trigger client-side events (JSON for event data) |
| `HX-Trigger-After-Swap` | Trigger events after swap |
| `HX-Trigger-After-Settle` | Trigger events after settle |

**Response status codes:**
- **204 No Content** — No swap is performed
- **2xx** — Normal swap
- **4xx/5xx** — Triggers `htmx:responseError`, no swap by default (configurable via `htmx:beforeSwap`)

## Events

### Key Lifecycle Events
```
htmx:configRequest → htmx:beforeRequest → htmx:beforeSend →
htmx:afterOnLoad → htmx:beforeSwap → htmx:afterSwap →
htmx:afterSettle → htmx:afterRequest
```

### Commonly Used Events
- `htmx:configRequest` — Modify parameters/headers before request
- `htmx:beforeSwap` — Configure swap behavior, handle error responses
- `htmx:afterSwap` — Run code after content is swapped
- `htmx:afterSettle` — Run code after DOM has settled
- `htmx:load` — New content loaded into DOM (use for initializing JS plugins)
- `htmx:confirm` — Async confirmation support
- `htmx:responseError` — HTTP error response
- `htmx:sendError` — Network error

### Inline Event Handling
```html
<button hx-get="/data" hx-on:htmx:before-request="showSpinner()">Load</button>
<button hx-on:click="handleClick(event)">Click</button>
```

Events fire in both camelCase (`htmx:beforeSwap`) and kebab-case (`htmx:before-swap`). Use kebab-case in `hx-on:` attributes.

### Handling Error Responses
```javascript
document.body.addEventListener('htmx:beforeSwap', function(evt) {
    if (evt.detail.xhr.status === 422) {
        evt.detail.shouldSwap = true;  // Allow swap on 422
        evt.detail.isError = false;
    }
});
```

## JavaScript API

```javascript
htmx.ajax('GET', '/url', '#target')           // Issue AJAX request
htmx.ajax('GET', '/url', {target: '#target', swap: 'outerHTML'})
htmx.process(document.getElementById('new'))  // Initialize htmx on dynamic content
htmx.on('htmx:afterSwap', function(evt) {})  // Listen for events
htmx.off('htmx:afterSwap', handler)           // Remove listener
htmx.onLoad(function(content) {})              // Callback when content loaded
htmx.find('#selector')                         // Find element
htmx.findAll('.selector')                      // Find all elements
htmx.closest(elt, '.selector')                 // Find closest ancestor
htmx.trigger(elt, 'eventName', {detail: {}})  // Trigger event
htmx.values(elt)                               // Get input values for element
htmx.remove(elt)                               // Remove element
htmx.addClass(elt, 'class')                   // Add class
htmx.removeClass(elt, 'class')                // Remove class
htmx.toggleClass(elt, 'class')                // Toggle class
htmx.swap(target, content, {swapStyle: 'innerHTML'})  // Programmatic swap
```

## Configuration

Set via JavaScript or meta tag:
```html
<meta name="htmx-config" content='{"selfRequestsOnly": true, "defaultSwapStyle": "outerHTML"}'>
```

| Option | Default | Description |
|--------|---------|-------------|
| `historyEnabled` | `true` | Enable history snapshots |
| `historyCacheSize` | `10` | Number of pages cached |
| `defaultSwapStyle` | `innerHTML` | Default swap method |
| `defaultSwapDelay` | `0` | Swap delay (ms) |
| `defaultSettleDelay` | `20` | Settle delay (ms) |
| `includeIndicatorStyles` | `true` | Load indicator CSS |
| `selfRequestsOnly` | `true` | Restrict to same-domain requests |
| `allowEval` | `true` | Allow eval-based features |
| `allowScriptTags` | `true` | Process `<script>` tags in responses |
| `timeout` | `0` | Request timeout (ms), 0 = none |
| `withCredentials` | `false` | Send credentials cross-origin |
| `scrollBehavior` | `instant` | `instant`, `smooth`, or `auto` |
| `globalViewTransitions` | `false` | Use View Transition API |
| `methodsThatUseUrlParams` | `["get","delete"]` | Methods using URL params |
| `refreshOnHistoryMiss` | `false` | Full refresh on history miss |
| `getCacheBusterParam` | `false` | Append cache buster to GETs |
| `ignoreTitle` | `false` | Ignore `<title>` in responses |

## Extensions

Enable with `hx-ext="name"` on a parent element (commonly `<body>`):

```html
<body hx-ext="head-support, preload">
```

**Core extensions:**
- `head-support` — Merge `<head>` tag changes from responses
- `idiomorph` — Morphing swap algorithm (preserves state, animations)
- `preload` — Preload content on `mousedown`/`mouseover`
- `response-targets` — Target different elements based on response status codes (`hx-target-*="selector"`)
- `sse` — Server-Sent Events support
- `ws` — WebSocket support
- `htmx-1-compat` — Backward compatibility with htmx 1.x

### Server-Sent Events (SSE)
```html
<div hx-ext="sse" sse-connect="/events">
  <div sse-swap="message">Waiting for messages...</div>
  <div sse-swap="eventName">Waiting for eventName...</div>
</div>
```

### WebSockets
```html
<div hx-ext="ws" ws-connect="/ws">
  <form ws-send>
    <input name="message">
    <button>Send</button>
  </form>
</div>
```

## Security Best Practices

1. **Always escape user content** — Prevent XSS by escaping all user-generated content in server responses
2. **Use `hx-disable`** — Prevent htmx processing in sections containing untrusted content
3. **Keep `selfRequestsOnly: true`** (default) — Restricts requests to the same domain
4. **CSRF protection** — Include tokens via `hx-headers`:
   ```html
   <body hx-headers='{"X-CSRF-TOKEN": "token-value"}'>
   ```
5. **Disable eval if possible** — Set `allowEval: false` and `allowScriptTags: false` for stricter CSP
6. **Use `hx-history="false"`** — On pages with sensitive data to prevent caching
7. **Content Security Policy** — Use nonce-based CSP with `inlineScriptNonce` and `inlineStyleNonce` config

## Common UI Patterns

### Click to Edit
```html
<div hx-get="/edit/1" hx-trigger="click" hx-swap="outerHTML">Click to edit</div>
```

### Active Search (with debounce)
```html
<input type="search" name="q"
       hx-get="/search"
       hx-trigger="input changed delay:300ms, search"
       hx-target="#results"
       hx-indicator="#search-spinner">
```

### Infinite Scroll
```html
<tr hx-get="/page/2"
    hx-trigger="revealed"
    hx-swap="afterend">
  <td>Loading...</td>
</tr>
```

### Lazy Loading
```html
<div hx-get="/lazy-content" hx-trigger="load" hx-swap="outerHTML">
  <span class="htmx-indicator">Loading...</span>
</div>
```

### Polling
```html
<div hx-get="/status" hx-trigger="every 5s">Current status</div>
```

### Delete with Confirmation
```html
<button hx-delete="/item/1"
        hx-confirm="Are you sure?"
        hx-target="closest tr"
        hx-swap="outerHTML swap:500ms">
  Delete
</button>
```

### Inline Validation
```html
<input name="email" hx-get="/validate/email"
       hx-trigger="change"
       hx-target="next .error">
<span class="error"></span>
```

### Dependent Selects (Value Select)
```html
<select name="make" hx-get="/models" hx-target="#models">
  <option value="audi">Audi</option>
  <option value="toyota">Toyota</option>
</select>
<select id="models" name="model">...</select>
```

### File Upload with Progress
```html
<form hx-post="/upload" hx-encoding="multipart/form-data"
      hx-indicator="#progress">
  <input type="file" name="file">
  <button>Upload</button>
  <progress id="progress" class="htmx-indicator" value="0" max="100"></progress>
</form>
```

### Tabs (HATEOAS)
```html
<div hx-target="#tab-content">
  <button hx-get="/tab/1" class="selected">Tab 1</button>
  <button hx-get="/tab/2">Tab 2</button>
  <button hx-get="/tab/3">Tab 3</button>
</div>
<div id="tab-content">Tab 1 content</div>
```

### Modal Dialog Pattern
```html
<button hx-get="/modal" hx-target="#modal-container" hx-swap="innerHTML">
  Open Modal
</button>
<div id="modal-container"></div>
```

### Form Reset After Submission
```html
<form hx-post="/submit" hx-target="#result" hx-on::after-request="this.reset()">
  <input name="field">
  <button>Submit</button>
</form>
```

## Server-Side Integration Notes

- HTMX expects **HTML fragment responses**, not JSON
- Use the `HX-Request` header to detect HTMX requests on the server
- Return partial HTML (just the fragment to swap), not full pages
- Use response headers (`HX-Trigger`, `HX-Redirect`, etc.) to control client behavior
- A 204 No Content response performs no swap
- For SPA-like navigation with boosting, return full page HTML and let htmx extract the body

## Reference Links

- Documentation: https://htmx.org/docs/
- Reference: https://htmx.org/reference/
- Examples: https://htmx.org/examples/
- Extensions: https://htmx.org/extensions/
