# AGENTS.md

## Task: CSS-only font remediation for local theme files

Your job is to perform **font remediation in local theme CSS/SCSS/LESS files only**.

### Core principle

Local theme styles must use **approved font families only**, and **must not load fonts themselves**.  
All font loading is handled separately outside this task, typically in the page template/head.

---

## Scope

### In scope

- Local theme CSS, SCSS, LESS
- Variables, mixins, utility classes, component styles, shared styles
- Local `font-family`, `font-weight`, `font-style` usage
- Local `@font-face` definitions that embed or load fonts inside theme styles

### Out of scope

- Template/head changes
- HTML changes
- JS-only font logic unless directly tied to CSS font class naming
- Vendor-owned third-party widget code
- External integrations that manage their own font delivery

---

## Hard rules

1. **Do not add font loading to CSS**
   - Do not add `@import` for fonts
   - Do not add CDN font URLs
   - Do not add or keep `@font-face`
   - Do not keep base64/data URI font sources
   - Do not self-host or inline fonts in local CSS as part of this remediation

2. **Remove legacy/local font loading from theme CSS**
   - If local CSS contains `@font-face`, embedded base64 fonts, or legacy font URLs, remove them once no longer referenced
   - Font loading must not remain in local theme CSS after remediation

3. **Replace non-approved fonts with approved fonts**
   - If a font family is not approved and not explicitly exempted, replace it according to the mapping rules below

4. **Preserve visual hierarchy**
   - Preserve intended typography by mapping old font variants into the correct `font-weight` and `font-style`

5. **At the end, always report the required `<head>` snippet**
   - If the final remediated CSS uses Google-hosted approved fonts, provide the exact HTML `<link>` snippet to insert into `<head>`
   - If the final approved font is not available through Google Fonts, clearly say so and do not invent a Google Fonts URL

---

## Font name normalization rules

Before making a decision, normalize every font family name:

- lowercase everything
- remove quotes
- remove spaces
- remove hyphens
- ignore formatting differences where relevant

Examples:

- `"Helvetica Neue"` -> `helveticaneue`
- `"Arial Black"` -> `arialblack`
- `"Avenir Next"` -> `avenirnext`
- `"Gotham SSm A"` -> `gothamssma`
- `"Roboto Condensed"` -> `robotocondensed`

Use the normalized name for decision-making.

---

## Approved font families

The following are approved examples from current remediation rules:

- `Roboto`
- `Roboto Condensed`
- `Montserrat`
- `NewHeroAccess`

If a font family is already approved:

- keep the approved family
- remove any local CSS-based loading
- normalize usage across styles
- keep or correct weights/styles as needed

---

## Explicit mapping rules

Apply these mappings directly:

- `helvetica` -> `Roboto`
- `helveticaneue` -> `Roboto`
- `arial` -> `Roboto`
- `arialblack` -> `Roboto`
- `segoeui` -> `Roboto`

- `robotocondensed` -> `Roboto Condensed`
- `montserrat` -> `Montserrat`
- `newheroaccess` -> `NewHeroAccess`

---

## Default replacement rule

If a local font is:

- not approved
- not in the explicit mapping list
- not a third-party exception
- and is used in local theme CSS

then treat it as a **non-approved legacy/custom font** and replace it with:

- `Roboto` by default
- `Roboto Condensed` if the original font clearly represents a condensed/narrow/compressed family

Examples of fonts that should normally be replaced with `Roboto`:

- `Avenir Next`
- `Gotham`
- `Gotham SSm A`
- `Gotham SSm B`
- `ArialMTProGrk-Light`
- `Proxima Nova`
- `Futura`
- other local/custom sans-serif legacy families

### Important interpretation rule

Do **not** try to preserve the original non-approved family name.  
The family name must be replaced with the approved one.  
Only the **visual intent** should be preserved through `font-weight` and `font-style`.

---

## Condensed family rule

If the old font name clearly signals a condensed/narrow/compressed variant, use:

- `Roboto Condensed`

Examples of indicators:

- `Condensed`
- `Narrow`
- `Compressed`

If there is no such signal, use:

- `Roboto`

---

## Weight and style preservation rules

When replacing a font family, preserve typography intent using `font-weight` and `font-style`.

Map name-based variants as follows:

- `Thin` -> `100`
- `ExtraLight`, `UltraLight` -> `200`
- `Light` -> `300`
- `Regular`, `Book`, `Roman`, `Normal` -> `400`
- `Medium` -> `500`
- `SemiBold`, `DemiBold` -> `600`
- `Bold` -> `700`
- `ExtraBold`, `Heavy` -> `800`
- `Black` -> `900`

Style mapping:

- `Italic`, `Oblique` -> `font-style: italic`
- otherwise -> `font-style: normal`

If `font-weight` is already explicitly present in CSS:

- keep it unless it clearly conflicts with the old font variant name and needs correction

### Example

- `Avenir Next Light` -> `font-family: 'Roboto', sans-serif; font-weight: 300;`
- `Gotham SSm A` with `font-weight: 500` -> `font-family: 'Roboto', sans-serif; font-weight: 500;`
- `ArialMTProGrk-Light` -> `font-family: 'Roboto', sans-serif; font-weight: 300;`

---

## Third-party exceptions

Do not remediate fonts inside vendor-owned third-party integrations or widget-owned code.

Known examples:

- `founders-grotesk-regular` -> Bazaarvoice-related third-party font
- `Metropolis` -> UserWay-related third-party font

Rules:

- If the font belongs to vendor-owned widget code, leave vendor code alone
- If that font was incorrectly copied or embedded into local theme CSS, remove the local embedding
- Do not rewrite vendor-managed code as part of local theme remediation unless explicitly instructed

---

## CSS output rules

After remediation, local CSS should contain only:

- approved font families
- correct `font-weight`
- correct `font-style`
- simple fallback stacks

Preferred fallback examples:

- `'Roboto', sans-serif`
- `'Roboto Condensed', sans-serif`
- `'Montserrat', sans-serif`
- `'NewHeroAccess', sans-serif`

Do not leave behind:

- old non-approved family names
- redundant fallback chains centered around removed legacy fonts
- unused `@font-face`
- embedded base64 fonts
- font CDN imports inside CSS

---

## Required decision flow for every font encountered

For each local font family found in theme CSS:

1. Normalize the font name
2. Check if it is an approved family
   - if yes, keep it and clean up any local loading
3. Check if it matches an explicit mapping rule
   - if yes, replace accordingly
4. Check if it is a third-party/vendor exception
   - if yes, do not remediate vendor-owned code
5. Otherwise treat it as a non-approved local legacy font
   - replace with `Roboto`
   - or `Roboto Condensed` if clearly condensed/narrow
6. Preserve weight/style using mapping rules
7. Remove obsolete local font loading
8. Update all local CSS references consistently

---

## Final response requirements

At the end of the task, always provide:

### 1. Summary of what was changed

- which old font families were removed
- which approved font families replaced them
- whether any local `@font-face` / base64 font definitions were removed

### 2. Head update requirements

List which approved fonts now need to be loaded in `<head>`.

### 3. Ready-to-paste HTML snippet for Google Fonts

If the final approved fonts are available on Google Fonts, provide the exact snippet.

Examples:

#### If only Roboto is needed

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@100;300;400;500;700;800;900&display=swap" rel="stylesheet">
```

#### If only Roboto Condensed is needed

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@300;400;700&display=swap" rel="stylesheet">
```

#### If only Montserrat is needed

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
```

#### If multiple Google Fonts are needed

Combine them into one optimized Google Fonts request whenever practical.

Example:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@100;300;400;500;700;800;900&family=Roboto+Condensed:wght@300;400;700&display=swap" rel="stylesheet">
```

### 4. Non-Google approved fonts

If the final approved family is not a Google Font, do not fabricate a Google Fonts snippet.
Instead say clearly:

- which font is required
- that it must be loaded from its approved non-Google source
- that no Google Fonts `<link>` can be generated for it from the current rules

Example:

- `NewHeroAccess` is approved but not assumed to be Google-hosted; load it from the approved site-owned/licensed source outside CSS.

---

## Success criteria

The task is complete only when:

- local theme CSS references only approved font families
- legacy/custom font-family names are removed
- no fonts are loaded from CSS
- weight/style hierarchy is preserved as closely as possible
- obsolete local `@font-face` blocks are removed
- the final response includes the required `<head>` HTML snippet for any Google-hosted approved fonts used after remediation

---

## Default uncertainty rule

If uncertain whether a non-approved font should map to `Roboto` or another approved family, default to `Roboto` unless an explicit project mapping says otherwise.

## Additional remediation rules from QA/testing findings

### 1. Approved fonts must not be local

Even if the final approved font is correct (for example `Roboto`), it is still a failure if it is loaded from local theme assets such as `/fonts/RobotoRegular.ttf`, local `@font-face`, base64 sources, or theme-hosted font files.
If an approved Google-hosted font is used, local CSS must only reference the family name and must not load the font from local assets.

### 2. Simplify font stacks aggressively

Do not leave legacy or suspicious fallback stacks after remediation.
When replacing a font family, collapse the stack to the approved family plus the generic fallback only, for example:

- `'Roboto', sans-serif`
- `'Roboto Condensed', sans-serif`
- `'Montserrat', sans-serif`

Do not keep old fallback entries such as:

- `Arial`
- `Helvetica`
- `Helvetica Neue`
- `Segoe UI`
- `-apple-system`
- `BlinkMacSystemFont`
- `Open Sans`
- `Source Sans Pro`
- `Noto Sans`
- other non-approved latin fallback families

These stacks can cause QA tools to report those fonts as actually used across the site.

### 3. Local custom font families must be removed even if paired with Arial/sans-serif

If CSS contains patterns like:

- `"MetaPro Black", Arial, sans-serif`
- `Roboto, Arial, sans-serif`
- `"GothamPro", Helvetica, Arial, sans-serif`

then the entire old stack must be rewritten to the approved final stack only.
Do not leave `Arial` or `Helvetica` as fallback after remediation.

### 4. Expand explicit default replacement coverage

Treat the following families as non-approved legacy/custom fonts unless a project-specific approved mapping says otherwise:

- `MetaPro`
- `Gilroy`
- `Gotham`
- `Gotham Pro`
- `Gotham Narrow`
- `Gotham SSm`
- `Avenir`
- `Avenir Next`
- `Inter`
- `Mulish`
- `Nunito`
- `Public Sans`
- `Source Sans Pro`
- `Open Sans`
- `Noto Sans`

Default mapping:

- use `Roboto`
- use `Roboto Condensed` only when the original family is clearly condensed/narrow/compressed or when the family is a condensed-style brand replacement

Examples:

- `Gotham Narrow` -> `Roboto Condensed`
- `Oswald` -> `Roboto Condensed`
- `MetaPro`, `Gilroy`, `Inter`, `Nunito`, `Open Sans` -> `Roboto`

### 5. Remove obsolete local font assets after CSS cleanup

If local CSS no longer references legacy fonts, remove or report obsolete font assets from theme-owned font folders.
This includes old `.ttf`, `.otf`, `.woff`, `.woff2`, and embedded base64 sources that belonged to removed local typography.
Do not keep dead font files in the theme when they are part of the remediated typography layer.

### 6. Vendor assets are exceptions, but only for vendor functionality

Do not treat vendor icon/widget assets as site typography that must be remapped.
Examples:

- `fontawesome`
- `slick`
- vendor widget fonts/assets

Rule:

- if they are part of icons, sliders, or third-party widget rendering, leave them alone
- if they were copied into local typography CSS and used as text fonts, remediate them

### 7. Inline styles and template-level font declarations must be audited too

The task may be CSS-first, but remediation is not complete if legacy fonts remain in:

- inline styles
- template fragments
- embedded style blocks
- CMS-managed rich text or template CSS blocks

If the current task scope does not allow editing those files, explicitly report them as remaining remediation items.
Do not report the theme as fully remediated when legacy fonts still exist outside CSS.

### 8. Invalid/custom aliases must be removed

If a font stack contains invalid or unexplained aliases such as:

- `clean`
- unexplained internal aliases
- suspicious fake family names

remove them unless there is a clearly documented and approved reason to keep them.

### 9. Presence in assets is not enough; actual references matter

Do not rewrite fonts only because a file exists in `/fonts`.
A font must be remediated when it is:

- referenced in local CSS
- loaded through local `@font-face`
- present in inline/template styles
- visible in actual runtime usage/network initiated by local theme CSS

Unused font files may be reported for cleanup, but active references are the higher priority.

### 10. Locale-specific fallbacks need special handling

For non-Latin sites (for example Japanese), do not blindly remove all system fallback fonts if they are needed for script coverage.
Examples:

- `Meiryo`
- `YuGothic`
- `Hiragino Kaku Gothic ProN`
- `MS PGothic`
- `Osaka`

Rules:

- remove invalid aliases and legacy latin fonts from the same stack
- keep locale-specific fallbacks only if they are necessary for script rendering and there is no approved project-specific replacement for that script
- still simplify the stack as much as possible
- if uncertain, report the locale-specific chain for manual review instead of making an unsafe replacement

### 11. QA success condition is runtime-based, not only source-based

The remediation is successful only when:

- local CSS no longer loads fonts
- local CSS references only approved families
- legacy/custom families are removed from source
- old fonts do not appear in runtime inspection as site typography loaded by theme CSS
- fallback stacks no longer cause Arial/Helvetica/Segoe UI/Open Sans/etc. to appear as site fonts in QA tools

### 12. Final reporting must include unresolved non-CSS font issues

If QA screenshots or inspection reveal remaining font issues outside editable CSS scope, the final report must include:

- remaining inline/template font declarations
- remaining local font asset loading
- remaining suspicious font stacks
- vendor exceptions left intentionally untouched
- any locale-specific fallback chains that require manual review
