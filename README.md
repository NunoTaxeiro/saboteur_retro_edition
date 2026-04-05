# SABOTEUR - Retro Edition

<img width="1026" height="782" alt="saboteur_gui" src="https://github.com/user-attachments/assets/ccb70cf9-cf59-4dd5-be28-f1e2c5adee3a" />


A retro 8/16-bit implementation of the classic card game Saboteur by Frederic Moyersoen, built with Python and Pygame.

## How to Play

You are a dwarf -- either a **Gold Miner** digging tunnels to find treasure, or a **Saboteur** trying to block the miners. Your role is secret!

### Rules
- **3 rounds**, each with secretly assigned roles
- Build a tunnel path from the **Start** card to one of 3 face-down **Goal** cards (only 1 has treasure)
- **Miners** want to connect the path to the treasure
- **Saboteurs** want to prevent it
- After 3 rounds, the dwarf with the most gold nuggets wins!

### Card Types
| Card | Description |
|------|-------------|
| **Path cards** | Build tunnels on the board (tan/sandy color) |
| **Dead-end cards** | Look like paths but are blocked inside (dark color, red X) |
| **Broken Tool** (red, XP/XL/XC) | Disable a player from placing path cards |
| **Fix Tool** (green, +P/+L/+C) | Repair a player's broken tool |
| **Rockfall** (brown, RF) | Remove any path card from the board |
| **Map** (blue, MAP) | Peek at a face-down goal card |

## Controls

| Key/Action | Effect |
|------------|--------|
| **Left Click** card in hand | Select card |
| **Left Click** board position | Place selected path card (green highlights = valid) |
| **Right Click** card in hand | Discard card (pass turn) |
| **R** | Rotate selected path card 180 degrees |
| **Arrow Keys / WASD** | Pan the board camera |
| **ESC** | Cancel selection / Return to menu |
| **ENTER** | Confirm / Advance screens |

## Installation & Running

```bash
pip install pygame
python saboteur.py
```

## React HTML Integration

This repository now includes a React host page under `web/` that embeds the game in an HTML page using an iframe.

### 1) Start the React page

```bash
cd web
npm install
npm run dev
```

Open the local URL shown by Vite (usually `http://localhost:5173`).

### 2) Plug in the web game build

Build the web version with pygbag from the project root:

```bash
pip install pygbag
set PYTHONUTF8=1
python -m pygbag --build saboteur.py
```

Then copy generated files from `build/web/` into `web/public/saboteur-web/`.

The iframe points to:

`web/public/saboteur-web/index.html`

Right now that path contains a placeholder page. Replace the contents of `web/public/saboteur-web/` with your generated browser build of `saboteur.py` (for example from a Pygame-to-web toolchain such as pygbag).

Once copied, the game runs directly inside the React HTML page.

## Requirements
- Python 3.8+
- Pygame 2.5+
