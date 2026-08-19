# Handoff: Profile Card UI Element

## Overview
A compact, self-contained profile card intended as a small test element for a native
Swift build system. It shows a user's identity (avatar, name, role), two summary stats
(posts, followers), and a Follow button that toggles between "Follow" and "Following".

## About the Design Files
The file in this bundle (`ProfileCard.dc.html`) is a **design reference created in HTML** —
a prototype showing the intended look and behavior, **not production code to copy directly**.
The task is to **recreate this design in the target codebase's environment**. The stated
target is **native Swift (SwiftUI)**; every element maps cleanly to SwiftUI primitives
(`VStack`/`HStack`, `Text`, `Button`, `@State`). Use the app's established patterns and
components where they exist.

## Fidelity
**High-fidelity (hifi).** Final colors, typography, spacing, and the follow-toggle
interaction are all specified below. Recreate pixel-for-pixel using native SwiftUI.

## Screens / Views

### Profile Card
- **Name**: ProfileCard
- **Purpose**: Display a person's identity + stats and let the viewer follow/unfollow them.
- **Layout**: A single vertical card centered on a light-gray backdrop.
  - Card container: fixed width **320px**, white background, corner radius **20px**,
    padding **24px** on all sides, drop shadow, vertical stack with **18px** gap between
    the three rows.
  - Row 1 — identity: horizontal stack, **14px** gap, vertically centered.
  - Row 2 — stats: horizontal stack, **24px** gap, **4px 2px** padding.
  - Row 3 — button: full-width button.

- **Components**:
  1. **Avatar** — 60×60, corner radius 30 (circle). Fill = linear gradient 135°, from
     `#0A84FF` to `#5E5CE6`. Centered initials "AJ", white, 24px, weight 600.
  2. **Name** — "Abbey Jackson", `#1C1C1E`, 18px, weight 600.
  3. **Role** — "Product Builder", `#8E8E93`, 14px, weight 400. (3px vertical gap below name.)
  4. **Stat: Posts** — value "128" (`#1C1C1E`, 17px, weight 700) over label "Posts"
     (`#8E8E93`, 12px, weight 500), 2px gap.
  5. **Stat: Followers** — value "2.4k" over label "Followers", same styling as Posts.
  6. **Follow button** — full width, corner radius 12px, padding 12px vertical, 15px, weight 600.
     - Default (not following): background `#0A84FF`, text `#FFFFFF`, label "Follow".
     - Following: background `#E5E5EA`, text `#1C1C1E`, label "Following".
     - Active/press: scale to 0.98.

## Interactions & Behavior
- Tapping the button toggles a boolean `following` state.
- Button label, background, and text color all switch on that state (see above).
- Press feedback: brief scale-down to 0.98 (transform transition ~0.1s ease); background
  transitions ~0.2s ease.
- No navigation, network, loading, or error states.

## State Management
- One boolean: `following` (default `false`).
- Toggled by the button's tap handler. Drives button label + colors.
- SwiftUI: `@State private var following = false`.

## Design Tokens
Colors:
- Background (screen): `#F2F2F7`
- Card surface: `#FFFFFF`
- Primary text: `#1C1C1E`
- Secondary text: `#8E8E93`
- Accent / primary button: `#0A84FF`
- Avatar gradient: `#0A84FF` → `#5E5CE6` (135°)
- Neutral / "Following" button: `#E5E5EA`
- Button text on accent: `#FFFFFF`

Spacing: 2, 3, 4, 14, 18, 24 (px)

Corner radius: card 20, avatar 30 (circular), button 12

Typography (Inter in the prototype; use SF Pro / system font natively):
- Name: 18 / 600
- Role: 14 / 400
- Stat value: 17 / 700
- Stat label: 12 / 500
- Avatar initials: 24 / 600
- Button: 15 / 600

Shadow: card `0 8px 30px rgba(0,0,0,0.08)`

## Assets
None. The avatar is a gradient-filled circle with text initials — no image files. The
prototype loads the Inter web font; natively, use the system font (SF Pro).

## Files
- `ProfileCard.dc.html` — the HTML design reference (open in a browser to view/interact).
