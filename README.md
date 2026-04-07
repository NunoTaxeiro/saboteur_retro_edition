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

### 2) Build and publish the web game

Use the build script from the project root:

```powershell
pip install pygbag
powershell -ExecutionPolicy Bypass -File .\scripts\build-web.ps1
```

What the script does:
- rebuilds the lightweight pygbag package from the current `saboteur.py`
- syncs it into `web_build_src/`
- publishes versioned `.apk` and `.tar.gz` files into `web/public/saboteur-web/`
- patches the generated wrapper HTML with the working browser settings
- updates the React iframe cache stamp in `web/src/App.jsx`

Optional arguments:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-web.ps1 -Stamp 20260406_custom
powershell -ExecutionPolicy Bypass -File .\scripts\build-web.ps1 -PythonExe "C:\Path\To\python.exe"
```

After the script finishes, reload the Vite page and the iframe will point to the freshly published build in `web/public/saboteur-web/`.

## Requirements
- Python 3.8+
- Pygame 2.5+
