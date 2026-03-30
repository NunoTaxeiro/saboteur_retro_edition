#!/usr/bin/env python3
"""
SABOTEUR - A retro 8/16-bit card game
Based on the board game by Frederic Moyersoen
Built with Pygame
"""

import pygame
import random
import sys
import math
from collections import deque

# ══════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════

INTERNAL_W, INTERNAL_H = 512, 384
SCALE = 2
WIN_W, WIN_H = INTERNAL_W * SCALE, INTERNAL_H * SCALE
FPS = 30

CARD_S = 30
TUNNEL_W = 10

N, E, S, W = 0, 1, 2, 3
OPPOSITE = {N: S, S: N, E: W, W: E}
DIR_DELTA = {N: (0, -1), E: (1, 0), S: (0, 1), W: (-1, 0)}
DIR_NAMES = {N: "N", E: "E", S: "S", W: "W"}

START_POS = (0, 0)
GOAL_POSITIONS = [(8, -1), (8, 0), (8, 1)]

DWARF_NAMES = [
    "Thorin", "Balin", "Gimli", "Gloin", "Bifur",
    "Bofur", "Bombur", "Dwalin", "Nori", "Ori"
]

ROLE_DISTRIBUTION = {
    3:  (1, 3),
    4:  (1, 4),
    5:  (2, 4),
    6:  (2, 5),
    7:  (3, 5),
    8:  (3, 6),
    9:  (3, 7),
    10: (4, 7),
}

HAND_SIZES = {
    3: 6, 4: 6, 5: 6,
    6: 5, 7: 5,
    8: 4, 9: 4, 10: 4,
}

TOOL_TYPES = ("pick", "lamp", "cart")
TOOL_ICON = {"pick": "P", "lamp": "L", "cart": "C"}

# ══════════════════════════════════════════════════════════════
#  RETRO COLOR PALETTE
# ══════════════════════════════════════════════════════════════

C_BG        = (20, 16, 32)
C_BOARD_BG  = (36, 30, 50)
C_CARD_BG   = (74, 55, 40)
C_TUNNEL    = (194, 160, 110)
C_TUNNEL_DEAD = (130, 95, 65)
C_GOLD      = (255, 210, 60)
C_GOLD_DK   = (200, 160, 30)
C_START     = (60, 150, 60)
C_START_DK  = (40, 100, 40)
C_GOAL_HIDE = (90, 75, 110)
C_STONE     = (85, 78, 68)
C_TEXT      = (230, 230, 230)
C_TEXT_DIM  = (130, 130, 130)
C_TEXT_GOLD = (255, 220, 80)
C_HIGHLIGHT = (80, 200, 80, 120)
C_SELECT    = (255, 240, 80)
C_MINER     = (70, 130, 220)
C_SABOTEUR  = (220, 60, 60)
C_UI_BORDER = (75, 65, 95)
C_UI_BG     = (30, 25, 44)
C_BROKEN    = (200, 50, 50)
C_FIX       = (50, 180, 50)
C_MAP_BG    = (60, 80, 140)
C_ROCK_BG   = (120, 90, 50)
C_HAND_BG   = (25, 20, 38)
C_DISABLED  = (60, 55, 50)
C_WHITE     = (255, 255, 255)
C_BLACK     = (0, 0, 0)
C_RED       = (220, 50, 50)
C_GREEN     = (50, 200, 50)
C_BLUE      = (50, 100, 220)

# ══════════════════════════════════════════════════════════════
#  CARD CLASSES
# ══════════════════════════════════════════════════════════════

class PathCard:
    def __init__(self, openings, dead_end=False):
        self.openings = frozenset(openings)
        self.dead_end = dead_end
        self.flipped = False
        self.card_type = "path"

    def get_openings(self):
        if self.flipped:
            return frozenset(OPPOSITE[d] for d in self.openings)
        return self.openings

    def get_groups(self):
        o = self.get_openings()
        if not o:
            return []
        if self.dead_end:
            return [frozenset([d]) for d in o]
        return [o]

    def flip(self):
        self.flipped = not self.flipped

    def clone(self):
        c = PathCard(self.openings, self.dead_end)
        c.flipped = self.flipped
        return c


class StartCard(PathCard):
    def __init__(self):
        super().__init__({N, E, S, W}, False)
        self.card_type = "start"


class GoalCard(PathCard):
    def __init__(self, is_treasure):
        super().__init__({N, E, S, W}, False)
        self.is_treasure = is_treasure
        self.revealed = False
        self.card_type = "goal_treasure" if is_treasure else "goal_stone"

    def get_openings(self):
        if not self.revealed:
            return frozenset({N, E, S, W})
        return frozenset({N, E, S, W})


class ActionCard:
    def __init__(self, action_type):
        self.action_type = action_type
        self.card_type = "action"

    def is_break(self):
        return self.action_type.startswith("broken_")

    def is_fix(self):
        return self.action_type.startswith("fix_")

    def break_tool(self):
        return self.action_type.replace("broken_", "")

    def fix_tools(self):
        t = self.action_type.replace("fix_", "")
        return t.split("_")


# ══════════════════════════════════════════════════════════════
#  DECK CREATION
# ══════════════════════════════════════════════════════════════

def create_path_deck():
    deck = []
    templates = [
        ((N, E, S, W), False, 5),
        ((N, E, S),    False, 5),
        ((E, S, W),    False, 5),
        ((N, S),       False, 4),
        ((E, W),       False, 3),
        ((N, E),       False, 4),
        ((S, E),       False, 3),
        ((S, W),       False, 2),
        ((N, W),       False, 1),
        ((N, E, S, W), True,  1),
        ((N, E, S),    True,  1),
        ((E, S, W),    True,  1),
        ((N, S),       True,  1),
        ((E, W),       True,  1),
        ((N, E),       True,  1),
        ((S, W),       True,  1),
        ((S,),         True,  1),
        ((N,),         True,  1),
    ]
    for openings, dead, count in templates:
        for _ in range(count):
            deck.append(PathCard(openings, dead))
    return deck


def create_action_deck():
    deck = []
    actions = [
        ("broken_pick", 3), ("broken_lamp", 3), ("broken_cart", 3),
        ("fix_pick", 2), ("fix_lamp", 2), ("fix_cart", 2),
        ("fix_pick_lamp", 1), ("fix_pick_cart", 1), ("fix_lamp_cart", 1),
        ("rockfall", 3), ("map", 6),
    ]
    for atype, count in actions:
        for _ in range(count):
            deck.append(ActionCard(atype))
    return deck


def create_gold_deck():
    cards = []
    for _ in range(16):
        cards.append(1)
    for _ in range(8):
        cards.append(2)
    for _ in range(4):
        cards.append(3)
    random.shuffle(cards)
    return cards


# ══════════════════════════════════════════════════════════════
#  BOARD LOGIC
# ══════════════════════════════════════════════════════════════

def get_active_openings(board):
    """BFS from start card to find all active outward-facing openings."""
    active = set()
    if START_POS not in board:
        return active

    start = board[START_POS]
    queue = deque()

    for group in start.get_groups():
        for d in group:
            key = (START_POS, d)
            if key not in active:
                active.add(key)
                queue.append(key)

    while queue:
        pos, direction = queue.popleft()
        dx, dy = DIR_DELTA[direction]
        neighbor_pos = (pos[0] + dx, pos[1] + dy)

        if neighbor_pos not in board:
            continue

        neighbor = board[neighbor_pos]
        incoming = OPPOSITE[direction]

        for group in neighbor.get_groups():
            if incoming in group:
                for d in group:
                    if d != incoming:
                        key = (neighbor_pos, d)
                        if key not in active:
                            active.add(key)
                            queue.append(key)
                break

    return active


def is_connected_to_start(board, pos, card):
    """Check if placing card at pos would connect to start."""
    active = get_active_openings(board)
    card_openings = card.get_openings()

    for d in card_openings:
        dx, dy = DIR_DELTA[d]
        adj = (pos[0] + dx, pos[1] + dy)
        opp = OPPOSITE[d]
        if (adj, opp) in active:
            return True

    if not board and pos == START_POS:
        return True

    return False


def is_valid_placement(board, goals, pos, card):
    if pos in board:
        return False
    if pos in {gp for gp in goals}:
        return False

    has_neighbor = False
    card_openings = card.get_openings()

    for d in (N, E, S, W):
        dx, dy = DIR_DELTA[d]
        adj = (pos[0] + dx, pos[1] + dy)
        opp = OPPOSITE[d]

        if adj in board:
            has_neighbor = True
            adj_card = board[adj]
            adj_openings = adj_card.get_openings()
            if (d in card_openings) != (opp in adj_openings):
                return False

    if not has_neighbor:
        return False

    return is_connected_to_start(board, pos, card)


def get_valid_positions(board, goals, card):
    positions = set()
    for pos in board:
        for d in (N, E, S, W):
            dx, dy = DIR_DELTA[d]
            candidate = (pos[0] + dx, pos[1] + dy)
            if candidate not in board and candidate not in goals:
                if is_valid_placement(board, goals, candidate, card):
                    positions.add(candidate)
    return positions


def check_goals_reached(board, goals):
    """Return list of goal positions reachable from start."""
    active = get_active_openings(board)
    reached = []

    for goal_pos in goals:
        gx, gy = goal_pos
        for d in (N, E, S, W):
            dx, dy = DIR_DELTA[d]
            adj = (gx + dx, gy + dy)
            opp = OPPOSITE[d]
            if (adj, opp) in active:
                reached.append(goal_pos)
                break

    return reached


# ══════════════════════════════════════════════════════════════
#  PLAYER
# ══════════════════════════════════════════════════════════════

class Player:
    def __init__(self, index, name, is_human=False):
        self.index = index
        self.name = name
        self.is_human = is_human
        self.hand = []
        self.role = None
        self.broken_tools = set()
        self.gold_cards = []
        self.known_goals = {}
        self.suspicion = {}

    @property
    def total_gold(self):
        return sum(self.gold_cards)

    def can_place_path(self):
        return len(self.broken_tools) == 0


# ══════════════════════════════════════════════════════════════
#  GAME STATE
# ══════════════════════════════════════════════════════════════

class GameState:
    def __init__(self, num_players, num_humans=1):
        self.num_players = num_players
        self.num_humans = min(num_humans, num_players)
        self.players = []
        self.board = {}
        self.goals = {}
        self.deck = []
        self.discard = []
        self.gold_deck = []
        self.current_player = 0
        self.round_num = 0
        self.round_over = False
        self.miners_won = False
        self.last_path_player = -1
        self.messages = deque(maxlen=6)
        self.first_player = 0

        human_names = ["Player 1", "Player 2"]
        for i in range(num_players):
            if i < self.num_humans:
                name = human_names[i] if i < len(human_names) else f"Player {i+1}"
                p = Player(i, name, is_human=True)
            else:
                name = DWARF_NAMES[i % len(DWARF_NAMES)]
                p = Player(i, name, is_human=False)
            self.players.append(p)

        self.gold_deck = create_gold_deck()

    def add_message(self, msg):
        self.messages.append(msg)

    def setup_round(self):
        self.round_num += 1
        self.round_over = False
        self.miners_won = False
        self.last_path_player = -1
        self.board = {}
        self.goals = {}
        self.messages.clear()

        self.board[START_POS] = StartCard()

        goal_types = [True, False, False]
        random.shuffle(goal_types)
        for i, gpos in enumerate(GOAL_POSITIONS):
            self.goals[gpos] = GoalCard(goal_types[i])

        sab_count, miner_count = ROLE_DISTRIBUTION[self.num_players]
        roles = ["saboteur"] * sab_count + ["miner"] * miner_count
        random.shuffle(roles)
        for i, p in enumerate(self.players):
            p.hand = []
            p.broken_tools = set()
            p.role = roles[i]
            p.known_goals = {}
            p.suspicion = {j: 0.0 for j in range(self.num_players) if j != i}

        path_deck = create_path_deck()
        action_deck = create_action_deck()
        self.deck = path_deck + action_deck
        random.shuffle(self.deck)
        self.discard = []

        hand_size = HAND_SIZES[self.num_players]
        for p in self.players:
            for _ in range(hand_size):
                if self.deck:
                    p.hand.append(self.deck.pop())

        self.current_player = self.first_player
        self.add_message(f"=== Round {self.round_num} ===")

    def draw_card(self, player):
        if self.deck:
            player.hand.append(self.deck.pop())

    def next_turn(self):
        self.current_player = (self.current_player + 1) % self.num_players

    def check_round_end(self):
        if self.round_over:
            return True
        for p in self.players:
            if p.hand:
                return False
        if not self.deck:
            self.round_over = True
            self.miners_won = False
            return True
        return False

    def distribute_gold(self):
        miners = [p for p in self.players if p.role == "miner"]
        saboteurs = [p for p in self.players if p.role == "saboteur"]

        if self.miners_won:
            num_miners = len(miners)
            drawn = []
            for _ in range(num_miners):
                if self.gold_deck:
                    drawn.append(self.gold_deck.pop(0))
            drawn.sort(reverse=True)

            if self.last_path_player >= 0:
                finder = self.players[self.last_path_player]
                if finder.role == "miner" and drawn:
                    idx = miners.index(finder)
                    reordered = [finder] + miners[:idx] + miners[idx + 1:]
                else:
                    reordered = miners
            else:
                reordered = miners

            for i, p in enumerate(reordered):
                if i < len(drawn):
                    p.gold_cards.append(drawn[i])
        else:
            sab_count = len(saboteurs)
            if sab_count == 0:
                return
            nuggets_each = {1: 4, 2: 3, 3: 3, 4: 2}.get(sab_count, 2)
            for p in saboteurs:
                total = 0
                while total < nuggets_each and self.gold_deck:
                    val = self.gold_deck.pop(0)
                    p.gold_cards.append(val)
                    total += val

    def place_card(self, player_idx, card, pos):
        player = self.players[player_idx]
        if card in player.hand:
            player.hand.remove(card)
        self.board[pos] = card
        self.last_path_player = player_idx
        self.draw_card(player)

        reached = check_goals_reached(self.board, self.goals)
        for gpos in reached:
            goal = self.goals[gpos]
            if not goal.revealed:
                goal.revealed = True
                if goal.is_treasure:
                    self.board[gpos] = goal
                    del self.goals[gpos]
                    self.round_over = True
                    self.miners_won = True
                    self.add_message("GOLD FOUND! Miners win!")
                    return True
                else:
                    self.board[gpos] = goal
                    del self.goals[gpos]
                    self.add_message("Stone revealed...")
                    return False
        return False

    def play_break(self, player_idx, card, target_idx):
        player = self.players[player_idx]
        target = self.players[target_idx]
        tool = card.break_tool()
        if tool not in target.broken_tools:
            target.broken_tools.add(tool)
            player.hand.remove(card)
            self.discard.append(card)
            self.draw_card(player)
            return True
        return False

    def play_fix(self, player_idx, card, target_idx):
        player = self.players[player_idx]
        target = self.players[target_idx]
        tools = card.fix_tools()
        fixed = None
        for t in tools:
            if t in target.broken_tools:
                fixed = t
                break
        if fixed:
            target.broken_tools.discard(fixed)
            player.hand.remove(card)
            self.discard.append(card)
            self.draw_card(player)
            return True
        return False

    def play_rockfall(self, player_idx, card, pos):
        player = self.players[player_idx]
        if pos in self.board and pos != START_POS:
            removed = self.board[pos]
            if isinstance(removed, GoalCard) or isinstance(removed, StartCard):
                return False
            del self.board[pos]
            player.hand.remove(card)
            self.discard.append(card)
            self.discard.append(removed)
            self.draw_card(player)
            return True
        return False

    def play_map(self, player_idx, card, goal_pos):
        player = self.players[player_idx]
        if goal_pos in self.goals:
            goal = self.goals[goal_pos]
            player.known_goals[goal_pos] = goal.is_treasure
            player.hand.remove(card)
            self.discard.append(card)
            self.draw_card(player)
            return goal.is_treasure
        return None

    def pass_turn(self, player_idx, card_idx=None):
        player = self.players[player_idx]
        if player.hand and card_idx is not None and card_idx < len(player.hand):
            self.discard.append(player.hand.pop(card_idx))
        elif player.hand:
            self.discard.append(player.hand.pop())
        self.draw_card(player)


# ══════════════════════════════════════════════════════════════
#  AI LOGIC
# ══════════════════════════════════════════════════════════════

class AI:
    @staticmethod
    def take_turn(gs, player_idx):
        p = gs.players[player_idx]
        if not p.hand:
            gs.pass_turn(player_idx)
            gs.add_message(f"{p.name} passes (empty)")
            return

        is_sab = p.role == "saboteur"
        best_score = -9999
        best_action = None

        for i, card in enumerate(p.hand):
            if isinstance(card, PathCard):
                if not p.can_place_path():
                    continue
                for flipped in [False, True]:
                    card.flipped = flipped
                    positions = get_valid_positions(gs.board, gs.goals, card)
                    for pos in positions:
                        score = AI._score_path(gs, p, card, pos, is_sab)
                        if score > best_score:
                            best_score = score
                            best_action = ("path", i, pos, flipped)
                    card.flipped = False

            elif isinstance(card, ActionCard):
                if card.is_break():
                    tool = card.break_tool()
                    for j, target in enumerate(gs.players):
                        if j == player_idx:
                            continue
                        if tool in target.broken_tools:
                            continue
                        score = AI._score_break(gs, p, target, is_sab)
                        if score > best_score:
                            best_score = score
                            best_action = ("break", i, j)

                elif card.is_fix():
                    tools = card.fix_tools()
                    for j, target in enumerate(gs.players):
                        for t in tools:
                            if t in target.broken_tools:
                                score = AI._score_fix(gs, p, target, j == player_idx, is_sab)
                                if score > best_score:
                                    best_score = score
                                    best_action = ("fix", i, j)
                                break

                elif card.action_type == "rockfall":
                    for pos, bcard in list(gs.board.items()):
                        if pos == START_POS:
                            continue
                        if isinstance(bcard, (StartCard, GoalCard)):
                            continue
                        score = AI._score_rockfall(gs, p, bcard, pos, is_sab)
                        if score > best_score:
                            best_score = score
                            best_action = ("rockfall", i, pos)

                elif card.action_type == "map":
                    for gpos in gs.goals:
                        if gpos not in p.known_goals:
                            score = 8
                            if score > best_score:
                                best_score = score
                                best_action = ("map", i, gpos)

        discard_score = AI._best_discard_score(p, is_sab)
        if discard_score > best_score or best_action is None:
            idx = AI._pick_discard(p, is_sab)
            gs.pass_turn(player_idx, idx)
            gs.add_message(f"{p.name} discards a card")
            return

        kind = best_action[0]
        card_idx = best_action[1]
        card = p.hand[card_idx]

        if kind == "path":
            _, ci, pos, flipped = best_action
            card.flipped = flipped
            gs.place_card(player_idx, card, pos)
            de = " (dead-end)" if card.dead_end else ""
            gs.add_message(f"{p.name} builds tunnel{de}")

        elif kind == "break":
            _, ci, target_idx = best_action
            target = gs.players[target_idx]
            tool = card.break_tool()
            gs.play_break(player_idx, card, target_idx)
            gs.add_message(f"{p.name} breaks {target.name}'s {tool}!")

        elif kind == "fix":
            _, ci, target_idx = best_action
            target = gs.players[target_idx]
            gs.play_fix(player_idx, card, target_idx)
            gs.add_message(f"{p.name} fixes {target.name}'s tools")

        elif kind == "rockfall":
            _, ci, pos = best_action
            gs.play_rockfall(player_idx, card, pos)
            gs.add_message(f"{p.name} causes rockfall!")

        elif kind == "map":
            _, ci, gpos = best_action
            result = gs.play_map(player_idx, card, gpos)
            gs.add_message(f"{p.name} checks a map...")

    @staticmethod
    def _score_path(gs, player, card, pos, is_sab):
        score = 0
        treasure_pos = None
        for gpos, known in player.known_goals.items():
            if known:
                treasure_pos = gpos
                break

        for gpos in GOAL_POSITIONS:
            dist = abs(pos[0] - gpos[0]) + abs(pos[1] - gpos[1])
            if treasure_pos and gpos == treasure_pos:
                weight = 4
            elif treasure_pos and gpos != treasure_pos:
                weight = 0.5
            else:
                weight = 2
            closeness = max(0, 12 - dist) * weight
            if is_sab:
                closeness = -closeness
            score += closeness

        if card.dead_end:
            score += 15 if is_sab else -20

        if is_sab:
            score += random.uniform(-2, 2)

        return score

    @staticmethod
    def _score_break(gs, player, target, is_sab):
        if is_sab:
            return 12 + random.uniform(-2, 2)
        else:
            sus = player.suspicion.get(target.index, 0)
            return sus * 3 + random.uniform(-1, 1)

    @staticmethod
    def _score_fix(gs, player, target, is_self, is_sab):
        if is_self:
            return 14
        if is_sab:
            sus = player.suspicion.get(target.index, 0)
            return -sus * 2 + 5
        else:
            return 10 + random.uniform(-1, 1)

    @staticmethod
    def _score_rockfall(gs, player, bcard, pos, is_sab):
        if is_sab:
            if not bcard.dead_end:
                active = get_active_openings(gs.board)
                is_on_path = any((pos, d) in active for d in bcard.get_openings())
                return 12 if is_on_path else 2
            return -5
        else:
            if bcard.dead_end:
                return 10
            return -5

    @staticmethod
    def _best_discard_score(player, is_sab):
        if is_sab:
            for card in player.hand:
                if isinstance(card, PathCard) and not card.dead_end:
                    return 3
            return -2
        else:
            for card in player.hand:
                if isinstance(card, PathCard) and card.dead_end:
                    return 5
            return -2

    @staticmethod
    def _pick_discard(player, is_sab):
        best_idx = 0
        best_val = -999
        for i, card in enumerate(player.hand):
            val = 0
            if isinstance(card, PathCard):
                if is_sab and not card.dead_end:
                    val = 5
                elif not is_sab and card.dead_end:
                    val = 5
            if val > best_val:
                best_val = val
                best_idx = i
        return best_idx


# ══════════════════════════════════════════════════════════════
#  RENDERER
# ══════════════════════════════════════════════════════════════

class Renderer:
    TOP_H = 52
    HAND_H = 76
    BOARD_Y = 52
    HAND_CARD_S = 34

    def __init__(self, surface):
        self.surf = surface
        self.font = pygame.font.Font(None, 14)
        self.font_md = pygame.font.Font(None, 18)
        self.font_lg = pygame.font.Font(None, 24)
        self.font_xl = pygame.font.Font(None, 36)
        self.tick = 0

    @property
    def board_h(self):
        return INTERNAL_H - self.TOP_H - self.HAND_H

    def draw_card_on_surface(self, card, size=CARD_S, highlight=False):
        s = pygame.Surface((size, size))
        s.fill(C_CARD_BG)
        t = size // 3
        openings = card.get_openings()

        if card.card_type == "start":
            color = C_START
            ctr_color = C_START_DK
        elif card.dead_end:
            color = C_TUNNEL_DEAD
            ctr_color = C_CARD_BG
        else:
            color = C_TUNNEL
            ctr_color = color

        if openings:
            pygame.draw.rect(s, ctr_color, (t, t, t, t))

        if N in openings:
            pygame.draw.rect(s, color, (t, 0, t, t))
        if S in openings:
            pygame.draw.rect(s, color, (t, 2 * t, t, t))
        if E in openings:
            pygame.draw.rect(s, color, (2 * t, t, t, t))
        if W in openings:
            pygame.draw.rect(s, color, (0, t, t, t))

        if card.dead_end and openings:
            cx, cy = size // 2, size // 2
            pygame.draw.line(s, C_BROKEN, (cx - 3, cy - 3), (cx + 3, cy + 3), 2)
            pygame.draw.line(s, C_BROKEN, (cx + 3, cy - 3), (cx - 3, cy + 3), 2)

        if card.card_type == "start":
            txt = self.font.render("S", True, C_WHITE)
            s.blit(txt, (size // 2 - txt.get_width() // 2, size // 2 - txt.get_height() // 2))

        if isinstance(card, GoalCard) and card.revealed:
            if card.is_treasure:
                pygame.draw.rect(s, C_GOLD, (t + 2, t + 2, t - 4, t - 4))
            else:
                pygame.draw.rect(s, C_STONE, (t + 2, t + 2, t - 4, t - 4))

        pygame.draw.rect(s, (50, 42, 32), (0, 0, size, size), 1)
        if highlight:
            hl = pygame.Surface((size, size), pygame.SRCALPHA)
            hl.fill((255, 255, 100, 60))
            s.blit(hl, (0, 0))

        return s

    def draw_goal_hidden(self, size=CARD_S):
        s = pygame.Surface((size, size))
        s.fill(C_GOAL_HIDE)
        pygame.draw.rect(s, (70, 60, 90), (0, 0, size, size), 1)
        txt = self.font_md.render("?", True, C_TEXT_DIM)
        s.blit(txt, (size // 2 - txt.get_width() // 2, size // 2 - txt.get_height() // 2))
        return s

    def draw_action_card_surface(self, card, size=34):
        s = pygame.Surface((size, size))
        if card.is_break():
            s.fill(C_BROKEN)
            tool = card.break_tool()
            lbl = "X" + TOOL_ICON.get(tool, "?")
        elif card.is_fix():
            s.fill(C_FIX)
            tools = card.fix_tools()
            lbl = "+".join(TOOL_ICON.get(t, "?") for t in tools)
        elif card.action_type == "rockfall":
            s.fill(C_ROCK_BG)
            lbl = "RF"
        elif card.action_type == "map":
            s.fill(C_MAP_BG)
            lbl = "MAP"
        else:
            s.fill(C_DISABLED)
            lbl = "?"

        pygame.draw.rect(s, C_WHITE, (0, 0, size, size), 1)
        txt = self.font.render(lbl, True, C_WHITE)
        s.blit(txt, (size // 2 - txt.get_width() // 2, size // 2 - txt.get_height() // 2))
        return s

    def draw_title(self):
        self.surf.fill(C_BG)
        pulse = (math.sin(self.tick * 0.06) + 1) / 2
        cr = int(200 + 55 * pulse)
        cg = int(180 + 40 * pulse)
        cb = int(30 + 30 * pulse)

        title = self.font_xl.render("SABOTEUR", True, (cr, cg, cb))
        self.surf.blit(title, (INTERNAL_W // 2 - title.get_width() // 2, 60))

        sub = self.font_md.render("The Dwarf Mining Game", True, C_TEXT_DIM)
        self.surf.blit(sub, (INTERNAL_W // 2 - sub.get_width() // 2, 100))

        pickaxe = [
            (0,-4),(1,-3),(2,-2),(3,-1),(4,0),(5,1),
            (1,-1),(2,0),(3,1),
            (-1,-3),(0,-2),(1,-1),
            (6,2),(7,3),
        ]
        ox, oy = INTERNAL_W // 2, 155
        for dx, dy in pickaxe:
            pygame.draw.rect(self.surf, C_GOLD, (ox + dx * 3, oy + dy * 3, 3, 3))
            pygame.draw.rect(self.surf, C_GOLD_DK, (ox - dx * 3, oy + dy * 3, 3, 3))

        for i in range(5):
            sparkle_x = int(ox + math.cos(self.tick * 0.04 + i * 1.3) * 60)
            sparkle_y = int(oy + math.sin(self.tick * 0.05 + i * 1.1) * 20)
            alpha = int(128 + 127 * math.sin(self.tick * 0.1 + i))
            if alpha > 180:
                pygame.draw.rect(self.surf, C_GOLD, (sparkle_x, sparkle_y, 2, 2))

        blink = self.tick % 60 < 40
        if blink:
            txt = self.font_md.render("Press ENTER to start", True, C_TEXT)
            self.surf.blit(txt, (INTERNAL_W // 2 - txt.get_width() // 2, 220))

        credit = self.font.render("by Nuno Taxeiro", True, C_TEXT_DIM)
        self.surf.blit(credit, (INTERNAL_W // 2 - credit.get_width() // 2, 340))
        ver = self.font.render("v1.0 - Retro Edition", True, (80, 80, 80))
        self.surf.blit(ver, (INTERNAL_W // 2 - ver.get_width() // 2, 355))

    def draw_setup(self, num_players, num_humans, setup_row):
        self.surf.fill(C_BG)
        title = self.font_lg.render("GAME SETUP", True, C_GOLD)
        self.surf.blit(title, (INTERNAL_W // 2 - title.get_width() // 2, 40))

        row0_col = C_SELECT if setup_row == 0 else C_TEXT
        row1_col = C_SELECT if setup_row == 1 else C_TEXT
        marker = "> " if True else "  "

        lbl0 = f"{'> ' if setup_row == 0 else '  '}Total Players:  < {num_players} >"
        lbl1 = f"{'> ' if setup_row == 1 else '  '}Human Players:  < {num_humans} >"

        pygame.draw.rect(self.surf, C_UI_BORDER if setup_row == 0 else C_UI_BG, (120, 88, 272, 30), 2)
        pygame.draw.rect(self.surf, C_UI_BORDER if setup_row == 1 else C_UI_BG, (120, 124, 272, 30), 2)

        txt0 = self.font_lg.render(lbl0, True, row0_col)
        txt1 = self.font_lg.render(lbl1, True, row1_col)
        self.surf.blit(txt0, (INTERNAL_W // 2 - txt0.get_width() // 2, 93))
        self.surf.blit(txt1, (INTERNAL_W // 2 - txt1.get_width() // 2, 129))

        sab, miners = ROLE_DISTRIBUTION[num_players]
        info = self.font.render(f"{miners} Miners  /  {sab} Saboteur{'s' if sab > 1 else ''}", True, C_TEXT_DIM)
        self.surf.blit(info, (INTERNAL_W // 2 - info.get_width() // 2, 170))

        hand_info = self.font.render(f"Cards per player: {HAND_SIZES[num_players]}", True, C_TEXT_DIM)
        self.surf.blit(hand_info, (INTERNAL_W // 2 - hand_info.get_width() // 2, 186))

        blink = self.tick % 60 < 40
        if blink:
            go = self.font_md.render("ENTER to start  |  UP/DOWN select row", True, C_TEXT)
            self.surf.blit(go, (INTERNAL_W // 2 - go.get_width() // 2, 230))

        if num_humans == 1:
            hint = self.font.render("Solo mode: You vs AI bots.", True, C_TEXT_DIM)
        else:
            hint = self.font.render(f"{num_humans} humans share this device (hot-seat).", True, C_TEXT_DIM)
        self.surf.blit(hint, (INTERNAL_W // 2 - hint.get_width() // 2, 300))

    def draw_game(self, gs, cam_x, cam_y, selected_card_idx, valid_positions, hover_grid,
                  phase, target_mode, map_reveal, map_reveal_timer):
        self.surf.fill(C_BG)
        self._draw_top_bar(gs)
        self._draw_board(gs, cam_x, cam_y, valid_positions, hover_grid, selected_card_idx, phase)
        self._draw_hand(gs, selected_card_idx, phase)
        self._draw_messages(gs)

        if map_reveal is not None and map_reveal_timer > 0:
            self._draw_map_popup(map_reveal)

        if target_mode:
            self._draw_target_selector(gs, selected_card_idx)

    def _draw_top_bar(self, gs):
        pygame.draw.rect(self.surf, C_UI_BG, (0, 0, INTERNAL_W, self.TOP_H))
        pygame.draw.line(self.surf, C_UI_BORDER, (0, self.TOP_H - 1), (INTERNAL_W, self.TOP_H - 1))

        rnd = self.font.render(f"Round {gs.round_num}/3", True, C_TEXT_GOLD)
        self.surf.blit(rnd, (4, 2))

        deck_txt = self.font.render(f"Deck:{len(gs.deck)}", True, C_TEXT_DIM)
        self.surf.blit(deck_txt, (80, 2))

        cp = gs.players[gs.current_player]
        turn_color = C_GREEN if cp.is_human else C_TEXT_DIM
        turn = self.font.render(f"Turn: {cp.name}", True, turn_color)
        self.surf.blit(turn, (140, 2))

        px = 4
        for i, p in enumerate(gs.players):
            is_current = i == gs.current_player
            col = C_SELECT if is_current else C_TEXT
            name = self.font.render(p.name[:6], True, col)
            self.surf.blit(name, (px, 16))

            gold_t = self.font.render(f"G:{p.total_gold}", True, C_GOLD)
            self.surf.blit(gold_t, (px, 28))

            bx = px
            for tool in TOOL_TYPES:
                if tool in p.broken_tools:
                    icon = self.font.render(TOOL_ICON[tool], True, C_BROKEN)
                    self.surf.blit(icon, (bx, 40))
                    bx += 10

            px += 52

    def _draw_board(self, gs, cam_x, cam_y, valid_positions, hover_grid, selected_idx, phase):
        board_y = self.BOARD_Y
        board_h = self.board_h
        board_rect = pygame.Rect(0, board_y, INTERNAL_W, board_h)
        pygame.draw.rect(self.surf, C_BOARD_BG, board_rect)

        cx = INTERNAL_W // 2
        cy = board_y + board_h // 2

        def grid_to_screen(gx, gy):
            sx = cx + gx * CARD_S - cam_x - CARD_S // 2
            sy = cy + gy * CARD_S - cam_y - CARD_S // 2
            return int(sx), int(sy)

        min_gx = int((cam_x - cx) / CARD_S) - 2
        max_gx = int((cam_x + cx) / CARD_S) + 3
        min_gy = int((cam_y - board_h // 2) / CARD_S) - 2
        max_gy = int((cam_y + board_h // 2) / CARD_S) + 3

        for gy in range(min_gy, max_gy):
            for gx in range(min_gx, max_gx):
                sx, sy = grid_to_screen(gx, gy)
                if sx < -CARD_S or sx > INTERNAL_W or sy < board_y - CARD_S or sy > board_y + board_h:
                    continue
                dot_x = sx + CARD_S // 2
                dot_y = sy + CARD_S // 2
                if board_y < dot_y < board_y + board_h:
                    self.surf.set_at((dot_x, dot_y), (50, 44, 66))

                pos = (gx, gy)
                if pos in gs.board:
                    card_surf = self.draw_card_on_surface(gs.board[pos])
                    self.surf.blit(card_surf, (sx, sy))
                elif pos in gs.goals:
                    goal = gs.goals[pos]
                    if goal.revealed:
                        card_surf = self.draw_card_on_surface(goal)
                    else:
                        card_surf = self.draw_goal_hidden()
                    self.surf.blit(card_surf, (sx, sy))

        if phase == "placing" and valid_positions:
            for vpos in valid_positions:
                sx, sy = grid_to_screen(vpos[0], vpos[1])
                if 0 <= sx < INTERNAL_W and board_y <= sy < board_y + board_h:
                    hl = pygame.Surface((CARD_S, CARD_S), pygame.SRCALPHA)
                    pulse = int(40 + 30 * math.sin(self.tick * 0.15))
                    hl.fill((80, 200, 80, pulse))
                    self.surf.blit(hl, (sx, sy))

            if hover_grid and hover_grid in valid_positions:
                sx, sy = grid_to_screen(hover_grid[0], hover_grid[1])
                player = gs.players[gs.current_player]
                if selected_idx is not None and selected_idx < len(player.hand):
                    card = player.hand[selected_idx]
                    if isinstance(card, PathCard):
                        preview = self.draw_card_on_surface(card, highlight=True)
                        preview.set_alpha(180)
                        self.surf.blit(preview, (sx, sy))

        if phase == "rockfall":
            for pos, card in gs.board.items():
                if pos == START_POS or isinstance(card, (StartCard, GoalCard)):
                    continue
                sx, sy = grid_to_screen(pos[0], pos[1])
                if 0 <= sx < INTERNAL_W and board_y <= sy < board_y + board_h:
                    hl = pygame.Surface((CARD_S, CARD_S), pygame.SRCALPHA)
                    pulse = int(40 + 30 * math.sin(self.tick * 0.15))
                    hl.fill((200, 80, 80, pulse))
                    self.surf.blit(hl, (sx, sy))

        if phase == "map_select":
            for gpos in gs.goals:
                goal = gs.goals[gpos]
                if not goal.revealed:
                    sx, sy = grid_to_screen(gpos[0], gpos[1])
                    hl = pygame.Surface((CARD_S, CARD_S), pygame.SRCALPHA)
                    pulse = int(40 + 30 * math.sin(self.tick * 0.15))
                    hl.fill((80, 80, 200, pulse))
                    self.surf.blit(hl, (sx, sy))

        pygame.draw.rect(self.surf, C_UI_BORDER, board_rect, 1)

    def _draw_hand(self, gs, selected_idx, phase):
        player = gs.players[gs.current_player]
        hand_y = INTERNAL_H - self.HAND_H
        pygame.draw.rect(self.surf, C_HAND_BG, (0, hand_y, INTERNAL_W, self.HAND_H))
        pygame.draw.line(self.surf, C_UI_BORDER, (0, hand_y), (INTERNAL_W, hand_y))

        cs = self.HAND_CARD_S
        total_w = len(player.hand) * (cs + 4) - 4
        start_x = max(4, INTERNAL_W // 2 - total_w // 2)

        role_col = C_MINER if player.role == "miner" else C_SABOTEUR
        role_txt = self.font.render(f"Role: {player.role.upper()}", True, role_col)
        self.surf.blit(role_txt, (4, hand_y + 2))

        help_text = "Click card, then board | R=rotate | Right-click=discard"
        ht = self.font.render(help_text, True, C_TEXT_DIM)
        self.surf.blit(ht, (INTERNAL_W - ht.get_width() - 4, hand_y + 2))

        for i, card in enumerate(player.hand):
            x = start_x + i * (cs + 4)
            y = hand_y + 16

            is_sel = i == selected_idx
            if is_sel:
                y -= 4

            disabled = False
            if isinstance(card, PathCard) and not player.can_place_path():
                disabled = True

            if isinstance(card, PathCard):
                card_surf = self.draw_card_on_surface(card, size=cs)
            else:
                card_surf = self.draw_action_card_surface(card, size=cs)

            if disabled:
                dark = pygame.Surface((cs, cs), pygame.SRCALPHA)
                dark.fill((0, 0, 0, 120))
                card_surf.blit(dark, (0, 0))

            self.surf.blit(card_surf, (x, y))

            if is_sel:
                pygame.draw.rect(self.surf, C_SELECT, (x - 1, y - 1, cs + 2, cs + 2), 2)

            if isinstance(card, PathCard) and card.flipped:
                ft = self.font.render("F", True, C_TEXT_GOLD)
                self.surf.blit(ft, (x + cs - 8, y))

    def _draw_messages(self, gs):
        mx = INTERNAL_W - 170
        my = self.BOARD_Y + 4
        for i, msg in enumerate(gs.messages):
            txt = self.font.render(msg[:28], True, C_TEXT if i == len(gs.messages) - 1 else C_TEXT_DIM)
            self.surf.blit(txt, (mx, my + i * 12))

    def _draw_map_popup(self, is_treasure):
        pw, ph = 160, 80
        px = INTERNAL_W // 2 - pw // 2
        py = INTERNAL_H // 2 - ph // 2
        pygame.draw.rect(self.surf, C_UI_BG, (px, py, pw, ph))
        pygame.draw.rect(self.surf, C_GOLD if is_treasure else C_STONE, (px, py, pw, ph), 2)

        if is_treasure:
            txt = self.font_lg.render("TREASURE!", True, C_GOLD)
        else:
            txt = self.font_lg.render("Just stone...", True, C_STONE)
        self.surf.blit(txt, (px + pw // 2 - txt.get_width() // 2, py + 20))

        hint = self.font.render("(click to close)", True, C_TEXT_DIM)
        self.surf.blit(hint, (px + pw // 2 - hint.get_width() // 2, py + 55))

    def _draw_target_selector(self, gs, selected_idx):
        player = gs.players[gs.current_player]
        if selected_idx is None or selected_idx >= len(player.hand):
            return
        card = player.hand[selected_idx]
        if not isinstance(card, ActionCard):
            return

        pw, ph = 200, 46 + gs.num_players * 20
        px = INTERNAL_W // 2 - pw // 2
        py = 80
        pygame.draw.rect(self.surf, C_UI_BG, (px, py, pw, ph))
        pygame.draw.rect(self.surf, C_UI_BORDER, (px, py, pw, ph), 1)

        action_label = card.action_type.replace("_", " ").title()
        header = f"Use {action_label} on:"
        ht = self.font.render(header, True, C_TEXT)
        self.surf.blit(ht, (px + 8, py + 4))

        for i, p in enumerate(gs.players):
            col = C_TEXT
            if card.is_break():
                tool = card.break_tool()
                if tool in p.broken_tools:
                    col = C_DISABLED
            elif card.is_fix():
                tools = card.fix_tools()
                has_match = any(t in p.broken_tools for t in tools)
                if not has_match:
                    col = C_DISABLED

            label = f"[{i + 1}] {p.name}"
            if p.broken_tools:
                label += " (X:" + ",".join(TOOL_ICON[t] for t in p.broken_tools) + ")"
            txt = self.font.render(label, True, col)
            self.surf.blit(txt, (px + 12, py + 20 + i * 20))

        cancel = self.font.render("Click outside to cancel", True, C_TEXT_DIM)
        self.surf.blit(cancel, (px + pw // 2 - cancel.get_width() // 2, py + ph - 14))

    def draw_pass_device(self, player_name):
        self.surf.fill(C_BG)

        pw, ph = 300, 120
        px = INTERNAL_W // 2 - pw // 2
        py = INTERNAL_H // 2 - ph // 2
        pygame.draw.rect(self.surf, C_UI_BG, (px, py, pw, ph))
        pygame.draw.rect(self.surf, C_GOLD, (px, py, pw, ph), 2)

        header = self.font_lg.render("PASS THE DEVICE", True, C_GOLD)
        self.surf.blit(header, (INTERNAL_W // 2 - header.get_width() // 2, py + 15))

        name_txt = self.font_xl.render(player_name, True, C_TEXT)
        self.surf.blit(name_txt, (INTERNAL_W // 2 - name_txt.get_width() // 2, py + 45))

        blink = self.tick % 60 < 40
        if blink:
            hint = self.font_md.render("Press ENTER when ready", True, C_TEXT_DIM)
            self.surf.blit(hint, (INTERNAL_W // 2 - hint.get_width() // 2, py + 85))

        warn = self.font.render("Don't peek at the other player's cards!", True, C_SABOTEUR)
        self.surf.blit(warn, (INTERNAL_W // 2 - warn.get_width() // 2, py + ph + 20))

    def draw_round_end(self, gs):
        self.surf.fill(C_BG)
        if gs.miners_won:
            title = self.font_xl.render("GOLD FOUND!", True, C_GOLD)
        else:
            title = self.font_xl.render("TUNNEL BLOCKED!", True, C_SABOTEUR)
        self.surf.blit(title, (INTERNAL_W // 2 - title.get_width() // 2, 30))

        winner = "Miners win!" if gs.miners_won else "Saboteurs win!"
        wt = self.font_lg.render(winner, True, C_TEXT)
        self.surf.blit(wt, (INTERNAL_W // 2 - wt.get_width() // 2, 70))

        y = 110
        for p in gs.players:
            role_col = C_MINER if p.role == "miner" else C_SABOTEUR
            name_t = self.font_md.render(f"{p.name}", True, C_TEXT)
            role_t = self.font.render(f"({p.role})", True, role_col)
            gold_t = self.font.render(f"Gold: {p.total_gold}", True, C_GOLD)
            self.surf.blit(name_t, (100, y))
            self.surf.blit(role_t, (200, y))
            self.surf.blit(gold_t, (300, y))
            y += 18

        blink = self.tick % 60 < 40
        if blink:
            if gs.round_num < 3:
                cont = self.font_md.render("Press ENTER for next round", True, C_TEXT)
            else:
                cont = self.font_md.render("Press ENTER for final scores", True, C_TEXT)
            self.surf.blit(cont, (INTERNAL_W // 2 - cont.get_width() // 2, 340))

    def draw_game_end(self, gs):
        self.surf.fill(C_BG)
        pulse = (math.sin(self.tick * 0.08) + 1) / 2

        title = self.font_xl.render("GAME OVER", True, C_GOLD)
        self.surf.blit(title, (INTERNAL_W // 2 - title.get_width() // 2, 30))

        sorted_players = sorted(gs.players, key=lambda p: p.total_gold, reverse=True)
        winner = sorted_players[0]
        wt = self.font_lg.render(f"{winner.name} wins with {winner.total_gold} gold!", True, C_TEXT_GOLD)
        self.surf.blit(wt, (INTERNAL_W // 2 - wt.get_width() // 2, 75))

        y = 120
        for rank, p in enumerate(sorted_players):
            medal = ["1st", "2nd", "3rd"][rank] if rank < 3 else f"{rank + 1}th"
            col = C_GOLD if rank == 0 else C_TEXT
            txt = self.font_md.render(f"{medal}  {p.name:10s}  Gold: {p.total_gold}", True, col)
            self.surf.blit(txt, (120, y))
            y += 22

        for i in range(12):
            angle = self.tick * 0.03 + i * 0.52
            sx = int(INTERNAL_W // 2 + math.cos(angle) * (80 + 20 * pulse))
            sy = int(50 + math.sin(angle) * 20)
            bright = int(180 + 75 * math.sin(self.tick * 0.1 + i))
            pygame.draw.rect(self.surf, (bright, bright // 2, 0), (sx, sy, 3, 3))

        blink = self.tick % 60 < 40
        if blink:
            txt = self.font_md.render("Press ENTER to play again | ESC to quit", True, C_TEXT)
            self.surf.blit(txt, (INTERNAL_W // 2 - txt.get_width() // 2, 340))


# ══════════════════════════════════════════════════════════════
#  MAIN GAME
# ══════════════════════════════════════════════════════════════

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("SABOTEUR - Retro Edition")
        self.window = pygame.display.set_mode((WIN_W, WIN_H))
        self.surface = pygame.Surface((INTERNAL_W, INTERNAL_H))
        self.scanlines = self._make_scanlines()
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.surface)

        self.state = "title"
        self.num_players = 4
        self.num_humans = 1
        self.setup_row = 0
        self.gs = None

        self.cam_x = 0
        self.cam_y = 0
        self.selected_card = None
        self.valid_positions = set()
        self.hover_grid = None
        self.phase = "select"
        self.target_mode = False
        self.map_reveal = None
        self.map_reveal_timer = 0
        self.ai_timer = 0
        self.AI_DELAY = 18

    def _make_scanlines(self):
        s = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        for y in range(0, WIN_H, 4):
            pygame.draw.line(s, (0, 0, 0, 25), (0, y), (WIN_W, y))
        return s

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self.renderer.tick += 1
            self._handle_events()
            self._update()
            self._render()

    def _handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if self.state == "game" and self.phase != "select":
                        self._cancel_selection()
                    elif self.state == "game" and self.target_mode:
                        self._cancel_selection()
                    elif self.state in ("title", "game_end"):
                        pygame.quit()
                        sys.exit()
                    elif self.state == "setup":
                        self.state = "title"
                    elif self.state == "pass_device":
                        self.state = "game"
                    elif self.state == "game":
                        self.state = "title"

                elif ev.key == pygame.K_RETURN:
                    if self.state == "title":
                        self.state = "setup"
                    elif self.state == "setup":
                        self._start_game()
                    elif self.state == "pass_device":
                        self.state = "game"
                    elif self.state == "round_end":
                        if self.gs.round_num < 3:
                            self.gs.setup_round()
                            self.state = "game"
                            self._reset_turn_state()
                            cp = self.gs.players[self.gs.current_player]
                            if cp.is_human and self.gs.num_humans > 1:
                                self.state = "pass_device"
                        else:
                            self.state = "game_end"
                    elif self.state == "game_end":
                        self.state = "title"

                elif self.state == "setup":
                    if ev.key in (pygame.K_UP, pygame.K_w):
                        self.setup_row = 0
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        self.setup_row = 1
                    elif ev.key in (pygame.K_LEFT, pygame.K_a):
                        if self.setup_row == 0:
                            self.num_players = max(3, self.num_players - 1)
                            self.num_humans = min(self.num_humans, self.num_players)
                        else:
                            self.num_humans = max(1, self.num_humans - 1)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        if self.setup_row == 0:
                            self.num_players = min(10, self.num_players + 1)
                        else:
                            self.num_humans = min(self.num_humans + 1, min(2, self.num_players))

                elif self.state == "game":
                    self._handle_game_key(ev.key)

            elif ev.type == pygame.MOUSEBUTTONDOWN and self.state == "game":
                mx, my = ev.pos[0] // SCALE, ev.pos[1] // SCALE
                if ev.button == 1:
                    self._handle_left_click(mx, my)
                elif ev.button == 3:
                    self._handle_right_click(mx, my)

            elif ev.type == pygame.MOUSEMOTION and self.state == "game":
                mx, my = ev.pos[0] // SCALE, ev.pos[1] // SCALE
                self._handle_mouse_move(mx, my)

    def _cur_is_human(self):
        return self.gs and self.gs.players[self.gs.current_player].is_human

    def _handle_game_key(self, key):
        cam_speed = 8
        if key == pygame.K_LEFT or key == pygame.K_a:
            self.cam_x -= cam_speed * 4
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            self.cam_x += cam_speed * 4
        elif key == pygame.K_UP or key == pygame.K_w:
            self.cam_y -= cam_speed * 4
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.cam_y += cam_speed * 4
        elif key == pygame.K_r:
            if self._cur_is_human():
                self._rotate_selected()
        elif key == pygame.K_SPACE:
            if self._cur_is_human() and self.map_reveal is not None:
                self.map_reveal = None
                self.map_reveal_timer = 0

    def _handle_left_click(self, mx, my):
        if self.gs is None or self.gs.round_over:
            return
        if not self._cur_is_human():
            return

        pi = self.gs.current_player
        player = self.gs.players[pi]

        if self.map_reveal is not None:
            self.map_reveal = None
            self.map_reveal_timer = 0
            self._end_human_turn()
            return

        hand_y = INTERNAL_H - Renderer.HAND_H + 16
        cs = Renderer.HAND_CARD_S
        total_w = len(player.hand) * (cs + 4) - 4
        start_x = max(4, INTERNAL_W // 2 - total_w // 2)

        if hand_y - 6 <= my <= hand_y + cs + 4:
            for i in range(len(player.hand)):
                card_x = start_x + i * (cs + 4)
                if card_x <= mx <= card_x + cs:
                    if i == self.selected_card:
                        self._cancel_selection()
                    else:
                        self._select_card(i)
                    return

        if self.target_mode:
            pw = 200
            ph = 46 + self.gs.num_players * 20
            popup_x = INTERNAL_W // 2 - pw // 2
            popup_y = 80
            if popup_x <= mx <= popup_x + pw and popup_y <= my <= popup_y + ph:
                self._handle_target_click(mx, my)
            else:
                self._cancel_selection()
            return

        if self.phase in ("rockfall", "map_select"):
            self._handle_board_action_click(mx, my)
            return

        if self.phase == "placing" and self.hover_grid:
            if self.hover_grid in self.valid_positions:
                card = player.hand[self.selected_card]
                self.gs.place_card(pi, card, self.hover_grid)
                self.gs.add_message(f"{player.name} builds a tunnel")
                self._end_human_turn()
                return

    def _handle_right_click(self, mx, my):
        if self.gs is None or self.gs.round_over:
            return
        if not self._cur_is_human():
            return

        if self.target_mode or self.phase in ("rockfall", "map_select", "placing"):
            self._cancel_selection()
            return

        pi = self.gs.current_player
        player = self.gs.players[pi]
        hand_y = INTERNAL_H - Renderer.HAND_H + 16
        cs = Renderer.HAND_CARD_S
        total_w = len(player.hand) * (cs + 4) - 4
        start_x = max(4, INTERNAL_W // 2 - total_w // 2)

        if hand_y - 6 <= my <= hand_y + cs + 4:
            for i in range(len(player.hand)):
                card_x = start_x + i * (cs + 4)
                if card_x <= mx <= card_x + cs:
                    self.gs.pass_turn(pi, i)
                    self.gs.add_message(f"{player.name} discards a card")
                    self._end_human_turn()
                    return

    def _handle_mouse_move(self, mx, my):
        if self.phase in ("placing", "rockfall", "map_select"):
            board_y = Renderer.BOARD_Y
            board_h = self.renderer.board_h
            if board_y <= my <= board_y + board_h:
                cx_s = INTERNAL_W // 2
                cy_s = board_y + board_h // 2
                gx = math.floor((mx - cx_s + self.cam_x + CARD_S // 2) / CARD_S)
                gy = math.floor((my - cy_s + self.cam_y + CARD_S // 2) / CARD_S)
                self.hover_grid = (gx, gy)
            else:
                self.hover_grid = None

    def _handle_board_action_click(self, mx, my):
        if not self.hover_grid:
            return
        pi = self.gs.current_player
        player = self.gs.players[pi]
        card = player.hand[self.selected_card]

        if self.phase == "rockfall":
            pos = self.hover_grid
            if pos in self.gs.board and pos != START_POS:
                bc = self.gs.board[pos]
                if not isinstance(bc, (StartCard, GoalCard)):
                    self.gs.play_rockfall(pi, card, pos)
                    self.gs.add_message(f"{player.name} causes a rockfall!")
                    self._end_human_turn()

        elif self.phase == "map_select":
            pos = self.hover_grid
            if pos in self.gs.goals and not self.gs.goals[pos].revealed:
                result = self.gs.play_map(pi, card, pos)
                if result is not None:
                    self.map_reveal = result
                    self.map_reveal_timer = 90
                    self.gs.add_message(f"{player.name} checks the map...")
                    self.phase = "select"
                    self.selected_card = None

    def _handle_target_click(self, mx, my):
        pi = self.gs.current_player
        player = self.gs.players[pi]
        card = player.hand[self.selected_card]

        pw, ph = 200, 30 + self.gs.num_players * 20
        px = INTERNAL_W // 2 - pw // 2
        py = 80

        for i, p in enumerate(self.gs.players):
            ty = py + 20 + i * 20
            if px <= mx <= px + pw and ty <= my <= ty + 16:
                if card.is_break():
                    tool = card.break_tool()
                    if tool not in p.broken_tools:
                        if self.gs.play_break(pi, card, i):
                            self.gs.add_message(f"{player.name} breaks {p.name}'s {tool}!")
                            self.target_mode = False
                            self._end_human_turn()
                elif card.is_fix():
                    if self.gs.play_fix(pi, card, i):
                        tname = f"{p.name}'s"
                        self.gs.add_message(f"{player.name} fixes {tname} tools")
                        self.target_mode = False
                        self._end_human_turn()
                return

    def _select_card(self, idx):
        player = self.gs.players[self.gs.current_player]
        card = player.hand[idx]
        self.selected_card = idx
        self.target_mode = False

        if isinstance(card, PathCard):
            if not player.can_place_path():
                self.phase = "select"
                self.valid_positions = set()
                return
            self.valid_positions = get_valid_positions(self.gs.board, self.gs.goals, card)
            self.phase = "placing"
            self.target_mode = False

        elif isinstance(card, ActionCard):
            self.valid_positions = set()
            if card.action_type == "rockfall":
                self.phase = "rockfall"
                self.target_mode = False
            elif card.action_type == "map":
                has_hidden = any(not g.revealed for g in self.gs.goals.values())
                if has_hidden:
                    self.phase = "map_select"
                    self.target_mode = False
                else:
                    self.phase = "select"
            elif card.is_break() or card.is_fix():
                self.phase = "select"
                self.target_mode = True
            else:
                self.phase = "select"

    def _rotate_selected(self):
        if self.selected_card is None:
            return
        player = self.gs.players[self.gs.current_player]
        if self.selected_card >= len(player.hand):
            return
        card = player.hand[self.selected_card]
        if isinstance(card, PathCard):
            card.flip()
            if player.can_place_path():
                self.valid_positions = get_valid_positions(self.gs.board, self.gs.goals, card)

    def _cancel_selection(self):
        self.selected_card = None
        self.valid_positions = set()
        self.phase = "select"
        self.target_mode = False

    def _end_human_turn(self):
        self._cancel_selection()
        if self.gs.round_over or self.gs.check_round_end():
            self.gs.distribute_gold()
            self.gs.first_player = (self.gs.last_path_player + 1) % self.gs.num_players \
                if self.gs.last_path_player >= 0 else 0
            self.state = "round_end"
            return
        self.gs.next_turn()
        cp = self.gs.players[self.gs.current_player]
        if cp.is_human:
            if self.gs.num_humans > 1:
                self.state = "pass_device"
        else:
            self.ai_timer = self.AI_DELAY

    def _reset_turn_state(self):
        self._cancel_selection()
        self.cam_x = 0
        self.cam_y = 0
        self.ai_timer = 0
        self.map_reveal = None
        self.map_reveal_timer = 0
        cp = self.gs.players[self.gs.current_player]
        if not cp.is_human:
            self.ai_timer = self.AI_DELAY

    def _start_game(self):
        self.gs = GameState(self.num_players, self.num_humans)
        self.gs.setup_round()
        self.state = "game"
        self._reset_turn_state()
        cp = self.gs.players[self.gs.current_player]
        if cp.is_human and self.num_humans > 1:
            self.state = "pass_device"

    def _update(self):
        if self.map_reveal_timer > 0:
            self.map_reveal_timer -= 1

        if self.state != "game" or self.gs is None:
            return

        if self.gs.round_over:
            return

        cp = self.gs.players[self.gs.current_player]
        if cp.is_human:
            if not cp.hand and not self.gs.deck:
                self.gs.pass_turn(self.gs.current_player)
                self.gs.add_message(f"{cp.name} has no cards")
                self._end_human_turn()
            return

        if self.ai_timer > 0:
            self.ai_timer -= 1
            return

        AI.take_turn(self.gs, self.gs.current_player)

        if self.gs.round_over or self.gs.check_round_end():
            self.gs.distribute_gold()
            self.gs.first_player = (self.gs.last_path_player + 1) % self.gs.num_players \
                if self.gs.last_path_player >= 0 else 0
            self.state = "round_end"
            return

        self.gs.next_turn()
        next_cp = self.gs.players[self.gs.current_player]
        if next_cp.is_human:
            if self.gs.num_humans > 1:
                self.state = "pass_device"
        else:
            self.ai_timer = self.AI_DELAY

    def _render(self):
        if self.state == "title":
            self.renderer.draw_title()
        elif self.state == "setup":
            self.renderer.draw_setup(self.num_players, self.num_humans, self.setup_row)
        elif self.state == "pass_device":
            cp = self.gs.players[self.gs.current_player]
            self.renderer.draw_pass_device(cp.name)
        elif self.state == "game":
            self.renderer.draw_game(
                self.gs, self.cam_x, self.cam_y,
                self.selected_card, self.valid_positions,
                self.hover_grid, self.phase, self.target_mode,
                self.map_reveal, self.map_reveal_timer
            )
        elif self.state == "round_end":
            self.renderer.draw_round_end(self.gs)
        elif self.state == "game_end":
            self.renderer.draw_game_end(self.gs)

        scaled = pygame.transform.scale(self.surface, (WIN_W, WIN_H))
        self.window.blit(scaled, (0, 0))
        self.window.blit(self.scanlines, (0, 0))
        pygame.display.flip()


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    game = Game()
    game.run()
