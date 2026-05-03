"""
╔══════════════════════════════════════════════════════════╗
║           A N A G R A M   G A M E   v2.0               ║
║     Professional Pygame Edition — Neon Arcade Style     ║
╚══════════════════════════════════════════════════════════╝
Run: python anagram_game.py
Controls:
  • Click letter tiles to build answer
  • Click answer slots to return a letter
  • ENTER  → Submit
  • SPACE  → Shuffle tiles
  • H      → Hint (−20 pts penalty)
  • S      → Skip round
  • R      → Restart (on game-over screen)
"""

import pygame
import sys
import math
import random
import time

# ─────────────────────────────── INIT ────────────────────────────────
pygame.init()
pygame.font.init()

W, H = 900, 650
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("ANAGRAM — Neon Arcade Edition")
clock = pygame.time.Clock()

# ─────────────────────────────── COLOURS ─────────────────────────────
BG        = (8, 8, 18)
CARD      = (16, 16, 30)
BORDER    = (28, 28, 52)
NEON_C    = (0, 255, 200)     # cyan
NEON_P    = (180, 80, 255)    # purple
NEON_Y    = (255, 220, 0)     # yellow
NEON_R    = (255, 50, 100)    # red/pink
TEXT      = (220, 220, 255)
MUTED     = (80, 80, 120)
WHITE     = (255, 255, 255)
BLACK     = (0, 0, 0)

# ─────────────────────────────── FONTS ───────────────────────────────
def load_font(size, bold=False):
    try:
        return pygame.font.SysFont("couriernew", size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)

F_HUGE   = load_font(62, bold=True)
F_BIG    = load_font(38, bold=True)
F_MED    = load_font(26, bold=True)
F_SMALL  = load_font(19)
F_TINY   = load_font(14)

# ─────────────────────────────── WORD BANK ───────────────────────────
WORD_BANK = [
    ("ELEPHANT",  "ANIMALS",   "Largest land mammal with a trunk & tusks.",    38),
    ("LEOPARD",   "ANIMALS",   "Fast spotted big cat of Africa and Asia.",      34),
    ("DOLPHIN",   "ANIMALS",   "Highly intelligent playful marine mammal.",     34),
    ("FLAMINGO",  "ANIMALS",   "Pink wading bird known for one-leg standing.",  36),
    ("PYTHON",    "ANIMALS",   "One of the world's largest constrictors.",      30),
    ("PLANETS",   "SCIENCE",   "Celestial bodies that orbit a star.",           32),
    ("GRAVITY",   "SCIENCE",   "Force pulling all mass toward each other.",     32),
    ("NEUTRON",   "SCIENCE",   "Neutral particle found in the atom nucleus.",   34),
    ("BIOLOGY",   "SCIENCE",   "Scientific study of all living organisms.",     30),
    ("CRYSTAL",   "SCIENCE",   "Solid with a highly ordered atomic structure.", 34),
    ("JUPITER",   "SPACE",     "Largest planet in our solar system.",           32),
    ("ECLIPSE",   "SPACE",     "When one body blocks another's light.",         34),
    ("NEBULAE",   "SPACE",     "Interstellar clouds of gas and cosmic dust.",   34),
    ("COMETS",    "SPACE",     "Icy bodies that grow a tail near the Sun.",     30),
    ("VOLCANO",   "GEOGRAPHY", "Mountain that can erupt hot magma & ash.",      32),
    ("GLACIER",   "GEOGRAPHY", "A slow-moving river of compacted ice.",         32),
    ("ESTUARY",   "GEOGRAPHY", "Tidal mouth where a river meets the sea.",      34),
    ("TUNDRA",    "GEOGRAPHY", "Treeless arctic biome with permafrost.",        30),
    ("TRUMPET",   "MUSIC",     "Brass wind instrument with a flared bell.",     34),
    ("HARMONY",   "MUSIC",     "Combination of simultaneously sounded notes.",  34),
    ("MELODY",    "MUSIC",     "A tuneful sequence of musical pitches.",        30),
    ("GALLERY",   "ART",       "A space dedicated to displaying artworks.",     32),
    ("PALETTE",   "ART",       "Board on which an artist mixes colours.",       34),
    ("MOSAIC",    "ART",       "Art form made from small coloured fragments.",  30),
    ("LABYRINTH", "MYTH",      "Complex maze built by the craftsman Daedalus.", 42),
    ("PHOENIX",   "MYTH",      "Mythical bird reborn from its own ashes.",      34),
    ("MINOTAUR",  "MYTH",      "Half-man, half-bull beast of Greek legend.",    38),
]

TOTAL_ROUNDS = 8

# ─────────────────────────────── HELPERS ─────────────────────────────
def glow_text(surf, text, font, colour, x, y, glow_r=3, center=True):
    """Render text with a soft neon glow effect."""
    glow_col = tuple(min(255, c // 3) for c in colour)
    for dx in range(-glow_r, glow_r + 1):
        for dy in range(-glow_r, glow_r + 1):
            if dx == 0 and dy == 0:
                continue
            g = font.render(text, True, glow_col)
            r = g.get_rect(center=(x + dx, y + dy)) if center else g.get_rect(topleft=(x + dx, y + dy))
            surf.blit(g, r)
    s = font.render(text, True, colour)
    r = s.get_rect(center=(x, y)) if center else s.get_rect(topleft=(x, y))
    surf.blit(s, r)

def draw_rounded_rect(surf, colour, rect, radius=10, border=0, border_colour=None):
    pygame.draw.rect(surf, colour, rect, border_radius=radius)
    if border and border_colour:
        pygame.draw.rect(surf, border_colour, rect, border, border_radius=radius)

def lerp_colour(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def draw_text_wrapped(surf, text, font, colour, rect, line_spacing=4):
    words = text.split()
    lines = []
    line = []
    max_w = rect[2]
    for w in words:
        test = ' '.join(line + [w])
        if font.size(test)[0] <= max_w:
            line.append(w)
        else:
            if line:
                lines.append(' '.join(line))
            line = [w]
    if line:
        lines.append(' '.join(line))
    y = rect[1]
    for ln in lines:
        s = font.render(ln, True, colour)
        surf.blit(s, (rect[0], y))
        y += font.get_height() + line_spacing


# ─────────────────────────────── PARTICLE SYSTEM ─────────────────────
class Particle:
    def __init__(self, x, y, colour):
        self.x = x + random.uniform(-8, 8)
        self.y = y + random.uniform(-8, 8)
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 2
        self.life = 1.0
        self.decay = random.uniform(0.025, 0.055)
        self.colour = colour
        self.size = random.randint(3, 7)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12
        self.vx *= 0.97
        self.life -= self.decay
        return self.life > 0

    def draw(self, surf):
        alpha = int(self.life * 255)
        col = tuple(min(255, c) for c in self.colour) + (alpha,)
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, col, (self.size, self.size), self.size)
        surf.blit(s, (int(self.x) - self.size, int(self.y) - self.size))


particles = []

def burst(x, y, colour, n=25):
    for _ in range(n):
        particles.append(Particle(x, y, colour))


# ─────────────────────────────── TILE ────────────────────────────────
class LetterTile:
    TILE_W, TILE_H = 58, 64

    def __init__(self, letter, idx, x, y):
        self.letter = letter
        self.idx = idx
        self.target_x = x
        self.target_y = y
        self.x = x
        self.y = float(y - 80)          # start above, animate in
        self.used = False
        self.hover = False
        self.anim_in = 0.0              # 0→1
        self.wobble = random.uniform(0, math.tau)

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.TILE_W, self.TILE_H)

    def update(self, dt):
        self.wobble += dt * 1.8
        if self.anim_in < 1.0:
            self.anim_in = min(1.0, self.anim_in + dt * 4.5)
            t = self.anim_in
            # spring overshoot
            overshoot = math.sin(t * math.pi) * 12 * (1 - t)
            self.y = self.target_y - (1 - t) ** 2 * 80 - overshoot
        if self.used:
            self.x += (self.target_x - self.x) * 0.15

    def draw(self, surf, tick):
        if self.used:
            col = (20, 20, 38)
            border = BORDER
            alpha = 80
        else:
            hover_t = 1.0 if self.hover else 0.0
            col = lerp_colour(CARD, (20, 30, 50), hover_t)
            border = lerp_colour(BORDER, NEON_C, hover_t)
            alpha = 255

        # slight float on hover
        draw_y = self.y - (6 if self.hover and not self.used else 0)

        s = pygame.Surface((self.TILE_W, self.TILE_H), pygame.SRCALPHA)
        pygame.draw.rect(s, col + (alpha,), s.get_rect(), border_radius=10)
        pygame.draw.rect(s, border + (alpha,), s.get_rect(), 2, border_radius=10)

        if not self.used:
            txt_col = NEON_C if self.hover else TEXT
            txt = F_BIG.render(self.letter, True, txt_col)
            s.blit(txt, txt.get_rect(center=(self.TILE_W // 2, self.TILE_H // 2)))
        surf.blit(s, (int(self.x), int(draw_y)))


class AnswerSlot:
    SLOT_W, SLOT_H = 58, 64

    def __init__(self, idx, x, y):
        self.idx = idx
        self.x = x
        self.y = y
        self.letter = None
        self.tile_idx = None
        self.hover = False
        self.flash = 0.0         # 1→0 for correct flash
        self.hint = False

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.SLOT_W, self.SLOT_H)

    def draw(self, surf):
        filled = self.letter is not None
        flash_t = self.flash

        if flash_t > 0:
            col = lerp_colour(CARD, NEON_C, flash_t * 0.6)
            border = lerp_colour(NEON_C, CARD, 1 - flash_t)
        elif filled:
            col = (14, 28, 28)
            border = NEON_C if not self.hint else NEON_Y
        else:
            col = CARD
            border = lerp_colour(BORDER, NEON_P, 0.6 if self.hover else 0)

        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        pygame.draw.rect(surf, border, self.rect, 2, border_radius=10)

        # dashed empty slot
        if not filled:
            dash_col = MUTED
            dw = self.SLOT_W - 14
            dh = self.SLOT_H - 14
            dr = pygame.Rect(self.x + 7, self.y + 7, dw, dh)
            dash_len = 8
            for i in range(0, dw, dash_len * 2):
                pygame.draw.line(surf, dash_col,
                                 (dr.x + i, dr.y), (min(dr.x + i + dash_len, dr.right), dr.y), 1)
                pygame.draw.line(surf, dash_col,
                                 (dr.x + i, dr.bottom), (min(dr.x + i + dash_len, dr.right), dr.bottom), 1)
            for i in range(0, dh, dash_len * 2):
                pygame.draw.line(surf, dash_col,
                                 (dr.x, dr.y + i), (dr.x, min(dr.y + i + dash_len, dr.bottom)), 1)
                pygame.draw.line(surf, dash_col,
                                 (dr.right, dr.y + i), (dr.right, min(dr.y + i + dash_len, dr.bottom)), 1)

        if filled:
            txt_col = NEON_Y if self.hint else NEON_C
            glow_text(surf, self.letter, F_BIG, txt_col,
                      self.x + self.SLOT_W // 2,
                      self.y + self.SLOT_H // 2, glow_r=2)


# ─────────────────────────────── GAME STATE ──────────────────────────
class Game:
    STATE_PLAYING = "playing"
    STATE_WIN     = "win"
    STATE_FAIL    = "fail"
    STATE_GAMEOVER= "gameover"
    STATE_INTRO   = "intro"

    def __init__(self):
        self.state = self.STATE_INTRO
        self.intro_timer = 2.5
        self.reset()

    def reset(self):
        self.deck = random.sample(WORD_BANK, TOTAL_ROUNDS)
        self.round_idx = 0
        self.score = 0
        self.streak = 0
        self.combo = 0
        self.total_score = 0
        self.shake_timer = 0.0
        self.shake_offset = (0, 0)
        self.hint_used = False
        self.load_round()

    def load_round(self):
        entry = self.deck[self.round_idx]
        self.word, self.category, self.clue, self.time_max = entry
        self.time_left = float(self.time_max)
        self.state = self.STATE_PLAYING
        self.hint_used = False
        self.result_timer = 0.0

        # scramble (ensure different from answer)
        scrambled = list(self.word)
        for _ in range(30):
            random.shuffle(scrambled)
            if ''.join(scrambled) != self.word:
                break
        self.scrambled = scrambled

        gap = 10
        total_w = len(self.word) * (LetterTile.TILE_W + gap) - gap
        start_x = (W - total_w) // 2
        self.tiles = [
            LetterTile(ch, i, start_x + i * (LetterTile.TILE_W + gap), 340)
            for i, ch in enumerate(scrambled)
        ]

        total_sw = len(self.word) * (AnswerSlot.SLOT_W + gap) - gap
        start_sx = (W - total_sw) // 2
        self.slots = [
            AnswerSlot(i, start_sx + i * (AnswerSlot.SLOT_W + gap), 430)
            for i in range(len(self.word))
        ]

        self.answer_letters = []   # list of (char, tile_idx)
        self.particles_local = []

    def current_answer(self):
        return ''.join(c for c, _ in self.answer_letters)

    def pick_letter(self, tile: LetterTile):
        if tile.used or len(self.answer_letters) >= len(self.word):
            return
        slot_idx = len(self.answer_letters)
        self.answer_letters.append((tile.letter, tile.idx))
        tile.used = True
        slot = self.slots[slot_idx]
        slot.letter = tile.letter
        slot.tile_idx = tile.idx
        # mini burst
        burst(slot.x + AnswerSlot.SLOT_W // 2,
              slot.y + AnswerSlot.SLOT_H // 2, NEON_P, n=8)

    def return_letter(self, slot_idx):
        if slot_idx >= len(self.answer_letters):
            return
        removed = self.answer_letters[slot_idx:]
        self.answer_letters = self.answer_letters[:slot_idx]
        for _, t_idx in removed:
            self.tiles[t_idx].used = False
            self.slots[slot_idx].letter = None
            self.slots[slot_idx].tile_idx = None
            self.slots[slot_idx].hint = False
        for i in range(slot_idx, len(self.slots)):
            self.slots[i].letter = None
            self.slots[i].tile_idx = None
            self.slots[i].hint = False

    def shuffle_tiles(self):
        letters = [t.letter for t in self.tiles]
        random.shuffle(letters)
        for t, l in zip(self.tiles, letters):
            t.letter = l
        # re-link used letters
        for pos, (_, t_idx) in enumerate(self.answer_letters):
            pass   # slots already bound

    def use_hint(self):
        if self.hint_used:
            return
        self.hint_used = True
        filled = len(self.answer_letters)
        if filled >= len(self.word):
            return
        correct_ch = self.word[filled]
        # find an unused tile with that letter
        for tile in self.tiles:
            if not tile.used and tile.letter == correct_ch:
                self.answer_letters.append((tile.letter, tile.idx))
                tile.used = True
                slot = self.slots[filled]
                slot.letter = tile.letter
                slot.tile_idx = tile.idx
                slot.hint = True
                break

    def submit(self):
        if len(self.answer_letters) < len(self.word):
            self._shake()
            return
        ans = self.current_answer()
        if ans == self.word:
            time_bonus = int((self.time_left / self.time_max) * 100)
            hint_penalty = 20 if self.hint_used else 0
            self.combo = min(5, self.combo + 1)
            combo_mult = 1 + (self.combo - 1) * 0.25
            pts = max(10, int((50 + time_bonus - hint_penalty) * combo_mult))
            self.score += pts
            self.streak += 1
            self.last_pts = pts
            self._correct_flash()
            for slot in self.slots:
                burst(slot.x + AnswerSlot.SLOT_W // 2,
                      slot.y + AnswerSlot.SLOT_H // 2, NEON_C, n=12)
            self.state = self.STATE_WIN
            self.result_timer = 1.4
        else:
            self.combo = 0
            self.streak = 0
            self._shake()
            # clear answer
            self._clear_answer()

    def _clear_answer(self):
        for _, t_idx in self.answer_letters:
            self.tiles[t_idx].used = False
        self.answer_letters = []
        for s in self.slots:
            s.letter = None
            s.tile_idx = None
            s.hint = False

    def _correct_flash(self):
        for s in self.slots:
            s.flash = 1.0

    def _shake(self):
        self.shake_timer = 0.35

    def skip(self):
        self.combo = 0
        self.streak = 0
        self._advance()

    def _advance(self):
        self.round_idx += 1
        if self.round_idx >= TOTAL_ROUNDS:
            self.total_score = self.score
            self.state = self.STATE_GAMEOVER
        else:
            self.load_round()

    def update(self, dt):
        global particles

        # intro
        if self.state == self.STATE_INTRO:
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self.state = self.STATE_PLAYING
            return

        if self.state == self.STATE_GAMEOVER:
            return

        # update tiles
        for t in self.tiles:
            t.update(dt)

        # update slot flash
        for s in self.slots:
            if s.flash > 0:
                s.flash = max(0, s.flash - dt * 2.5)

        # particles
        particles = [p for p in particles if p.update()]

        # shake
        if self.shake_timer > 0:
            self.shake_timer -= dt
            amp = self.shake_timer * 18
            self.shake_offset = (
                math.sin(self.shake_timer * 60) * amp,
                math.cos(self.shake_timer * 45) * amp * 0.5
            )
        else:
            self.shake_offset = (0, 0)

        # timer
        if self.state == self.STATE_PLAYING:
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.combo = 0
                self.streak = 0
                self.state = self.STATE_FAIL
                self.result_timer = 1.8

        # auto advance after result
        if self.state in (self.STATE_WIN, self.STATE_FAIL):
            self.result_timer -= dt
            if self.result_timer <= 0:
                self._advance()

    def handle_click(self, pos):
        if self.state != self.STATE_PLAYING:
            return
        ox, oy = self.shake_offset
        adj = (pos[0] - ox, pos[1] - oy)

        # check slots first (return letter)
        for i, s in enumerate(self.slots):
            if s.rect.collidepoint(adj) and s.letter:
                self.return_letter(i)
                return

        # check tiles
        for t in self.tiles:
            if t.rect.collidepoint(adj) and not t.used:
                self.pick_letter(t)
                return

    def update_hover(self, pos):
        if self.state != self.STATE_PLAYING:
            return
        ox, oy = self.shake_offset
        adj = (pos[0] - ox, pos[1] - oy)
        for t in self.tiles:
            t.hover = t.rect.collidepoint(adj) and not t.used
        for s in self.slots:
            s.hover = s.rect.collidepoint(adj) and bool(s.letter)


# ─────────────────────────────── DRAW ────────────────────────────────
def draw_scanlines(surf):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(0, H, 4):
        pygame.draw.line(s, (0, 0, 0, 35), (0, y), (W, y))
    surf.blit(s, (0, 0))

def draw_grid(surf, tick):
    """Animated perspective grid background."""
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    col = (20, 20, 50, 60)
    spacing = 50
    offset = (tick * 12) % spacing
    for x in range(-spacing, W + spacing, spacing):
        pygame.draw.line(s, col, (x, 0), (x, H))
    for y in range(int(-offset), H + spacing, spacing):
        pygame.draw.line(s, col, (0, y), (W, y))
    surf.blit(s, (0, 0))

def draw_header(surf, game, tick):
    # title
    glow_text(surf, "ANAGRAM", F_HUGE, NEON_C, W // 2, 46, glow_r=4)

    # stat pills
    pill_data = [
        ("SCORE", str(game.score),  NEON_Y, 60),
        ("ROUND", f"{game.round_idx + 1}/{TOTAL_ROUNDS}", NEON_C, W // 2),
        ("STREAK", str(game.streak), NEON_P, W - 60),
    ]
    for label, val, col, cx in pill_data:
        pw, ph = 120, 52
        px = cx - pw // 2
        py = 76
        draw_rounded_rect(surf, CARD, (px, py, pw, ph), radius=8,
                          border=1, border_colour=BORDER)
        ls = F_TINY.render(label, True, MUTED)
        surf.blit(ls, ls.get_rect(center=(cx, py + 14)))
        vs = F_MED.render(val, True, col)
        surf.blit(vs, vs.get_rect(center=(cx, py + 35)))

def draw_combo_gems(surf, combo, tick):
    gem_size = 18
    gap = 8
    total = 5
    tw = total * (gem_size + gap) - gap
    sx = (W - tw) // 2
    y = 138
    label = F_TINY.render("COMBO", True, MUTED)
    surf.blit(label, label.get_rect(midright=(sx - 12, y + gem_size // 2)))
    for i in range(total):
        gx = sx + i * (gem_size + gap)
        lit = i < combo
        col = NEON_Y if lit else BORDER
        pygame.draw.rect(surf, col, (gx, y, gem_size, gem_size), border_radius=4)
        if lit:
            glow = pygame.Surface((gem_size + 12, gem_size + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow, NEON_Y + (60,), glow.get_rect(), border_radius=6)
            surf.blit(glow, (gx - 6, y - 6))

def draw_timer(surf, time_left, time_max):
    bar_w = W - 80
    bar_h = 8
    bx, by = 40, 162
    pct = max(0, time_left / time_max)
    # bg
    pygame.draw.rect(surf, BORDER, (bx, by, bar_w, bar_h), border_radius=4)
    # fill
    fill_w = int(bar_w * pct)
    if fill_w > 4:
        if pct > 0.5:
            col = NEON_C
        elif pct > 0.25:
            col = NEON_Y
        else:
            col = NEON_R
        pygame.draw.rect(surf, col, (bx, by, fill_w, bar_h), border_radius=4)
        # glow
        gs = pygame.Surface((fill_w, bar_h + 6), pygame.SRCALPHA)
        gc = col + (50,)
        pygame.draw.rect(gs, gc, gs.get_rect(), border_radius=4)
        surf.blit(gs, (bx, by - 3))

    time_s = F_TINY.render(f"{int(time_left)}s", True, MUTED)
    surf.blit(time_s, (bx + bar_w + 8, by - 2))

def draw_category_clue(surf, game):
    cat_col = {
        "ANIMALS": NEON_C, "SCIENCE": NEON_P, "SPACE": NEON_Y,
        "GEOGRAPHY": (80, 220, 120), "MUSIC": (255, 140, 80),
        "ART": (255, 80, 200), "MYTH": (180, 80, 255),
    }.get(game.category, NEON_C)

    # category badge
    cat_s = F_SMALL.render(f"◉  {game.category}", True, cat_col)
    cx = W // 2 - cat_s.get_width() // 2
    cy = 185
    badge_pad = 8
    badge_r = pygame.Rect(cx - badge_pad, cy - 3, cat_s.get_width() + badge_pad * 2, cat_s.get_height() + 6)
    badge_surf = pygame.Surface((badge_r.width, badge_r.height), pygame.SRCALPHA)
    badge_surf.fill(cat_col[:3] + (28,))
    surf.blit(badge_surf, badge_r.topleft)
    pygame.draw.rect(surf, cat_col + (90,), badge_r, 1, border_radius=6)
    surf.blit(cat_s, (cx, cy))

    # clue
    clue_rect = (60, 218, W - 120, 50)
    draw_text_wrapped(surf, game.clue, F_SMALL, MUTED, clue_rect)

def draw_progress_dots(surf, game):
    dot_r = 7
    gap = 18
    total = TOTAL_ROUNDS
    tw = total * (dot_r * 2 + gap) - gap
    sx = (W - tw) // 2
    y = 285
    for i in range(total):
        x = sx + i * (dot_r * 2 + gap) + dot_r
        if i < game.round_idx:
            pygame.draw.circle(surf, NEON_C, (x, y), dot_r)
        elif i == game.round_idx:
            t = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
            col = lerp_colour(NEON_Y, NEON_C, t)
            pygame.draw.circle(surf, col, (x, y), dot_r + 2)
        else:
            pygame.draw.circle(surf, BORDER, (x, y), dot_r)
            pygame.draw.circle(surf, MUTED, (x, y), dot_r, 1)

def draw_controls_hint(surf):
    hints = "[ENTER] Submit   [SPACE] Shuffle   [H] Hint   [S] Skip"
    s = F_TINY.render(hints, True, (50, 50, 80))
    surf.blit(s, s.get_rect(center=(W // 2, H - 22)))

def draw_result_overlay(surf, game):
    if game.state == game.STATE_WIN:
        overlay_col = (0, 255, 180, 22)
        title = "CORRECT!"
        title_col = NEON_C
        sub = f"+{game.last_pts} pts  |  Combo x{game.combo}"
        sub_col = NEON_Y
    elif game.state == game.STATE_FAIL:
        overlay_col = (255, 40, 80, 18)
        title = "TIME'S UP!"
        title_col = NEON_R
        sub = f"The word was: {game.word}"
        sub_col = MUTED
    else:
        return

    fade = pygame.Surface((W, H), pygame.SRCALPHA)
    fade.fill(overlay_col)
    surf.blit(fade, (0, 0))
    glow_text(surf, title, F_BIG, title_col, W // 2, H // 2 - 20, glow_r=5)
    s = F_SMALL.render(sub, True, sub_col)
    surf.blit(s, s.get_rect(center=(W // 2, H // 2 + 30)))

def draw_gameover(surf, game):
    surf.fill(BG)
    draw_grid(surf, pygame.time.get_ticks() / 1000)
    draw_scanlines(surf)

    glow_text(surf, "GAME OVER", F_HUGE, NEON_R, W // 2, 160, glow_r=6)
    glow_text(surf, "FINAL SCORE", F_MED, MUTED, W // 2, 250, glow_r=2)
    glow_text(surf, str(game.total_score), F_HUGE, NEON_Y, W // 2, 320, glow_r=5)

    pct = game.total_score / (TOTAL_ROUNDS * 180)
    if pct >= 0.8:
        grade, gcol = "LEGENDARY", NEON_Y
    elif pct >= 0.6:
        grade, gcol = "EXCELLENT", NEON_C
    elif pct >= 0.4:
        grade, gcol = "GOOD JOB", NEON_P
    else:
        grade, gcol = "KEEP TRYING", NEON_R

    glow_text(surf, grade, F_BIG, gcol, W // 2, 405, glow_r=4)

    # restart prompt
    t = (math.sin(pygame.time.get_ticks() * 0.004) + 1) / 2
    col = lerp_colour(MUTED, TEXT, t)
    rs = F_SMALL.render("[R] Play Again   [ESC] Quit", True, col)
    surf.blit(rs, rs.get_rect(center=(W // 2, 490)))

def draw_intro(surf, timer):
    surf.fill(BG)
    draw_grid(surf, pygame.time.get_ticks() / 1000)
    t = max(0, 1 - timer / 2.5)
    alpha = int(t * 255)
    glow_text(surf, "ANAGRAM", F_HUGE, NEON_C, W // 2, H // 2 - 30, glow_r=6)
    sub = F_MED.render("NEON ARCADE EDITION", True, NEON_P)
    sub.set_alpha(alpha)
    surf.blit(sub, sub.get_rect(center=(W // 2, H // 2 + 40)))

# ─────────────────────────────── MAIN LOOP ───────────────────────────
def main():
    game = Game()
    prev_time = time.time()
    tick = 0.0

    while True:
        now = time.time()
        dt = min(now - prev_time, 0.05)
        prev_time = now
        tick += dt

        # ── Events ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                if game.state == game.STATE_GAMEOVER:
                    if event.key == pygame.K_r:
                        game.reset()
                    continue

                if game.state == game.STATE_PLAYING:
                    if event.key == pygame.K_RETURN:
                        game.submit()
                    elif event.key == pygame.K_SPACE:
                        game.shuffle_tiles()
                    elif event.key == pygame.K_h:
                        game.use_hint()
                    elif event.key == pygame.K_s:
                        game.skip()
                    elif event.key == pygame.K_BACKSPACE:
                        if game.answer_letters:
                            game.return_letter(len(game.answer_letters) - 1)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.state == game.STATE_PLAYING:
                    game.handle_click(event.pos)

            if event.type == pygame.MOUSEMOTION:
                game.update_hover(event.pos)

        # ── Update ──
        game.update(dt)

        # ── Draw ──
        screen.fill(BG)
        draw_grid(screen, tick)

        if game.state == game.STATE_INTRO:
            draw_intro(screen, game.intro_timer)
        elif game.state == game.STATE_GAMEOVER:
            for p in particles:
                p.update()
                p.draw(screen)
            draw_gameover(screen, game)
        else:
            ox, oy = game.shake_offset

            # draw everything on offset surface for shake
            main_surf = pygame.Surface((W, H), pygame.SRCALPHA)

            draw_header(main_surf, game, tick)
            draw_combo_gems(main_surf, game.combo, tick)
            draw_timer(main_surf, game.time_left, game.time_max)
            draw_category_clue(main_surf, game)
            draw_progress_dots(main_surf, game)

            # tiles & slots
            for tile in game.tiles:
                tile.draw(main_surf, tick)
            for slot in game.slots:
                slot.draw(main_surf)

            # result overlay
            if game.state in (game.STATE_WIN, game.STATE_FAIL):
                draw_result_overlay(main_surf, game)

            screen.blit(main_surf, (int(ox), int(oy)))

            # particles (no shake)
            for p in particles:
                p.draw(screen)

            draw_controls_hint(screen)

        draw_scanlines(screen)
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
