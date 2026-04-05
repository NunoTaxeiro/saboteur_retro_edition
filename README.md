# SABOTEUR - Retro Edition

A retro 8/16-bit implementation of the classic card game Saboteur by Frederic Moyersoen, built with Python and Pygame.

## Latest Commit

- **Commit ID:** d46638fd8ed995f99fc49a9e836404b17ac635dd
- **Author:** NunoTaxeiro
- **Date:** 2026-04-04
- **Message:** [expand visible play area](https://github.com/NunoTaxeiro/saboteur_retro_edition/commit/d46638fd8ed995f99fc49a9e836404b17ac635dd)

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

## Requirements
- Python 3.8+
- Pygame 2.5+
