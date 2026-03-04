#!/usr/bin/env python3
"""
Two-Player Scoreboard Application
For Raspberry Pi 3 with joystick input — optimised build
"""

import pygame
import sys
import math

# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
pygame.init()
pygame.joystick.init()

for _idx in range(min(pygame.joystick.get_count(), 3)):
    _js = pygame.joystick.Joystick(_idx)
    _js.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Scoreboard")
width, height = screen.get_size()

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
BLUE      = (37,  99,  235)
RED       = (220, 38,  38)
GREY      = (75,  85,  99)
DARK_GREY = (45,  45,  45)
YELLOW    = (251, 191, 36)
GREEN     = (52,  211, 153)
WHITE     = (255, 255, 255)
BLACK     = (26,  26,  26)
ORANGE    = (255, 140, 0)

# ---------------------------------------------------------------------------
# Fonts — created ONCE at startup, never inside the render loop
# ---------------------------------------------------------------------------
score_font       = pygame.font.Font(None, 500)
title_mega_font  = pygame.font.Font(None, 400)
press_start_font = pygame.font.Font(None, 80)
over21_font      = pygame.font.Font(None, 140)
ret_font         = pygame.font.Font(None, 160)
sd_font          = pygame.font.Font(None, 220)
msg_font2        = pygame.font.Font(None, 62)
msg_font3        = pygame.font.Font(None, 60)
declare_font_sm  = pygame.font.Font(None, 50)
declare_font_md  = pygame.font.Font(None, 52)
dw_font          = pygame.font.Font(None, 110)
banner_font      = pygame.font.Font(None, 70)
ctrl_font        = pygame.font.Font(None, 42)
pop_font         = pygame.font.Font(None, 90)
sub_font2        = pygame.font.Font(None, 46)
cf_font          = pygame.font.Font(None, 130)
skeech_font      = pygame.font.Font(None, 80)

# ---------------------------------------------------------------------------
# Pre-rendered static text surfaces — render() never called inside the loop
# ---------------------------------------------------------------------------
def _r(font, text, color):
    return font.render(text, True, color)

surf_press_start_play   = _r(press_start_font,  "Press Start To Play",           YELLOW)
surf_press_again        = _r(press_start_font,  "Press Start To Play Again",     YELLOW)
surf_over21             = _r(over21_font,        "You Went Over!",                ORANGE)
surf_ret_title          = _r(ret_font,           "Retribution?",                  YELLOW)
surf_white_gameover     = _r(msg_font2,          "White Button = Game Over",      WHITE)
surf_black_retrib       = _r(msg_font2,          "Black Button = Retribution",    (20, 20, 20))
surf_declare_banner_rw  = _r(declare_font_sm,    "Press Black to Declare Winner", WHITE)
surf_declare_banner_sd  = _r(declare_font_md,    "Press Black to Declare Winner", WHITE)
surf_dw_confirm         = _r(msg_font3,          "Black Button = Confirm",        (20, 20, 20))
surf_dw_cancel          = _r(msg_font3,          "White Button = Cancel",         WHITE)
surf_dw_skeech          = _r(msg_font3,          "Blue Button = Skeech",          BLUE)
surf_edit_black_lbl     = _r(ctrl_font,          "Black = +1",                    (20, 20, 20))
surf_edit_white_lbl     = _r(ctrl_font,          "White = -1",                    WHITE)
surf_edit_p1_lbl        = _r(ctrl_font,          "P1 = Done",                     (180, 180, 255))
surf_edit_blue_lbl      = _r(ctrl_font,          "Blue = Skeech",                 BLUE)
surf_edit_blue_banner   = _r(banner_font,        "Edit Blue Score",               BLUE)
surf_edit_red_banner    = _r(banner_font,        "Edit Red Score",                RED)
surf_sc_press           = _r(sub_font2,          "Press ",                        WHITE)
surf_sc_blue            = _r(sub_font2,          "Blue",                          BLUE)
surf_sc_confirm         = _r(sub_font2,          " to confirm  or  ",             WHITE)
surf_sc_white_word      = _r(sub_font2,          "White",                         (220, 220, 220))
surf_sc_cancel          = _r(sub_font2,          " to cancel",                    WHITE)
surf_sc_blue_title      = _r(pop_font,           "Blue Skeech?",                  BLUE)
surf_sc_red_title       = _r(pop_font,           "Red Skeech?",                   RED)
surf_quit_title         = _r(cf_font,            "Exit Game?",                    YELLOW)
surf_quit_yes           = _r(msg_font2,          "White Button = Back to Menu",   WHITE)
surf_quit_no            = _r(msg_font2,          "Black Button = Cancel",         (20, 20, 20))
surf_quit_kill          = _r(msg_font2,          "Red Button = Kill App",         RED)
surf_skeeched           = _r(skeech_font,        "You got Skeeched!",             YELLOW)

SC_SUBLINE_W = (surf_sc_press.get_width()    + surf_sc_blue.get_width()     +
                surf_sc_confirm.get_width()  + surf_sc_white_word.get_width() +
                surf_sc_cancel.get_width())

# Score digits 0–21 pre-rendered; add extras on demand
_score_cache = {i: score_font.render(str(i), True, WHITE) for i in range(22)}

def get_score_surf(n):
    if n not in _score_cache:
        _score_cache[n] = score_font.render(str(n), True, WHITE)
    return _score_cache[n]

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
header_height     = 20
footer_height     = 20
scoreboard_height = height - header_height - footer_height
half_width        = width  // 2
score_center_y    = header_height + scoreboard_height // 2

_PAD_X, _PAD_Y, _ROW_GAP = 40, 24, 14

# ---------------------------------------------------------------------------
# Pre-built reusable surfaces
# ---------------------------------------------------------------------------
_overlay_surf = pygame.Surface((width, height), pygame.SRCALPHA)
_overlay_surf.fill((20, 20, 20, 220))

_grey_half = pygame.Surface((half_width, scoreboard_height))
_grey_half.set_alpha(128)
_grey_half.fill(GREY)

_edit_grey = pygame.Surface((half_width, scoreboard_height), pygame.SRCALPHA)
_edit_grey.fill((80, 80, 80, 180))

def _alpha_bg(w, h, alpha=150):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    return s

_bg_declare_rw = _alpha_bg(surf_declare_banner_rw.get_width() + 30,
                            surf_declare_banner_rw.get_height() + 10)
_bg_declare_sd = _alpha_bg(surf_declare_banner_sd.get_width() + 30,
                            surf_declare_banner_sd.get_height() + 14, alpha=160)

# Edit score bar
_bar_h  = 54
_bar_y  = height - footer_height - _bar_h - 6
_seg_w  = width // 4
_bar_bg = pygame.Surface((width, _bar_h))
_bar_bg.fill((30, 30, 30))

_seg_surfs = []
for _col in [(200, 200, 200), (60, 60, 60), DARK_GREY, (230, 230, 255)]:
    _s = pygame.Surface((_seg_w - 4, _bar_h - 4))
    _s.fill(_col)
    _seg_surfs.append(_s)

# Banner background for edit mode
_banner_bg_w = max(surf_edit_blue_banner.get_width(), surf_edit_red_banner.get_width()) + 40
_banner_bg_h = surf_edit_blue_banner.get_height() + 16
_banner_bg   = pygame.Surface((_banner_bg_w, _banner_bg_h))
_banner_bg.fill((20, 20, 20))

def _panel(w, h):
    s = pygame.Surface((w, h))
    s.fill((80, 85, 95))
    s.set_alpha(235)
    return s

def _light_strip(w, h):
    s = pygame.Surface((w, h))
    s.fill((215, 215, 215))
    return s

def _dark_strip(w, h, color=(20, 30, 80)):
    s = pygame.Surface((w, h))
    s.fill(color)
    return s

# Retribution panel
_ret_panel_w = max(surf_white_gameover.get_width(), surf_black_retrib.get_width()) + _PAD_X * 2
_ret_row_h   = surf_white_gameover.get_height() + _PAD_Y
_ret_panel_h = _ret_row_h * 2 + _PAD_Y + _ROW_GAP
_ret_panel_x = width  // 2 - _ret_panel_w // 2
_ret_panel_y = height // 2 - 10
_ret_panel_s = _panel(_ret_panel_w, _ret_panel_h)
_ret_strip   = _light_strip(_ret_panel_w - 6, _ret_row_h)

# Declare Winner panel (3 rows: confirm / cancel / skeech)
_dw_panel_w  = max(surf_dw_confirm.get_width(), surf_dw_cancel.get_width(),
                   surf_dw_skeech.get_width()) + _PAD_X * 2
_dw_row_h    = surf_dw_confirm.get_height() + _PAD_Y
_dw_panel_h  = _dw_row_h * 3 + _PAD_Y * 2 + _ROW_GAP * 2
_dw_panel_x  = width  // 2 - _dw_panel_w // 2
_dw_panel_y  = height // 2 - 20
_dw_panel_s  = _panel(_dw_panel_w, _dw_panel_h)
_dw_strip1   = _light_strip(_dw_panel_w - 6, _dw_row_h)
_dw_bstrip   = _dark_strip(_dw_panel_w - 6, _dw_row_h, (20, 30, 80))

# Quit panel (3 rows: menu / cancel / kill)
_quit_panel_w = max(surf_quit_yes.get_width(), surf_quit_no.get_width(),
                    surf_quit_kill.get_width()) + _PAD_X * 2
_quit_row_h   = surf_quit_yes.get_height() + _PAD_Y
_quit_panel_h = _quit_row_h * 3 + _PAD_Y + _ROW_GAP * 2
_quit_panel_x = width  // 2 - _quit_panel_w // 2
_quit_panel_y = height // 2 - 10
_quit_panel_s = _panel(_quit_panel_w, _quit_panel_h)
_quit_strip_no   = _light_strip(_quit_panel_w - 6, _quit_row_h)
_quit_strip_kill = _dark_strip(_quit_panel_w - 6, _quit_row_h, (60, 10, 10))

# Skeech confirm popup
_sc_pop_w  = max(surf_sc_blue_title.get_width(),
                 surf_sc_red_title.get_width(), SC_SUBLINE_W) + 80
_sc_pop_h  = 240
_sc_pop_x  = width  // 2 - _sc_pop_w // 2
_sc_pop_y  = height // 2 - _sc_pop_h // 2
_sc_pop_s  = pygame.Surface((_sc_pop_w, _sc_pop_h), pygame.SRCALPHA)
_sc_pop_s.fill((20, 20, 20, 240))

# Winner "Press Start" box
_psa_rect = surf_press_again.get_rect(center=(width // 2, height // 2 + 300))
_pad      = 20
_psa_box  = pygame.Rect(_psa_rect.x - _pad, _psa_rect.y - _pad,
                         _psa_rect.width + _pad * 2, _psa_rect.height + _pad * 2)

# ---------------------------------------------------------------------------
# Game states
# ---------------------------------------------------------------------------
STATE_WELCOME          = "welcome"
STATE_PLAYING          = "playing"
STATE_OVER_21          = "over_21"
STATE_RETRIBUTION      = "retribution"
STATE_RETRIBUTION_WAIT = "retribution_wait"
STATE_SUDDEN_DEATH     = "sudden_death"
STATE_WINNER           = "winner"
STATE_DECLARE_WINNER   = "declare_winner"
STATE_CONFIRM_QUIT     = "confirm_quit"
STATE_EDIT_SCORE       = "edit_score"
STATE_SKEECH_CONFIRM   = "skeech_confirm"

# ---------------------------------------------------------------------------
# GameState
# ---------------------------------------------------------------------------
class GameState:
    def __init__(self):
        self.player1_score = 0
        self.player2_score = 0
        self.game_active   = False
        self.winner        = None
        self.score_history = []
        self.pulse_time    = 0.0
        self.winner_announced_time   = None
        self.state                   = STATE_WELCOME
        self.over21_player           = None
        self.over21_start_time       = None
        self.retribution_player      = None
        self.retribution_start_time  = None
        self.sudden_death_start_time = None
        self.declare_winner_player   = None
        self.pre_declare_state       = None
        self.pre_quit_state          = None
        self.edit_player             = None
        self.pre_edit_state          = None
        self.skeech_winner           = None

    def go_to_welcome(self):
        self.__init__()

    def start_game(self):
        self.player1_score           = 0
        self.player2_score           = 0
        self.game_active             = True
        self.winner                  = None
        self.score_history           = []
        self.winner_announced_time   = None
        self.state                   = STATE_PLAYING
        self.over21_player           = None
        self.over21_start_time       = None
        self.retribution_player      = None
        self.retribution_start_time  = None
        self.sudden_death_start_time = None
        self.declare_winner_player   = None
        self.pre_declare_state       = None
        self.edit_player             = None
        self.pre_edit_state          = None
        self.skeech_winner           = None

    def add_score(self, player, points):
        if self.state not in (STATE_PLAYING, STATE_RETRIBUTION_WAIT):
            return
        if player == 1:
            self.score_history.append({'player': 1, 'prev': self.player1_score})
            self.player1_score += points
        else:
            self.score_history.append({'player': 2, 'prev': self.player2_score})
            self.player2_score += points
        self.check_score(player)

    def check_score(self, player):
        score = self.player1_score if player == 1 else self.player2_score
        if score > 21:
            if player == 1: self.player1_score = 15
            else:           self.player2_score = 15
            self.over21_player     = player
            self.over21_start_time = pygame.time.get_ticks()
            self.state             = STATE_OVER_21
        elif score == 21:
            if self.state == STATE_RETRIBUTION_WAIT:
                self.sudden_death_start_time = pygame.time.get_ticks()
                self.state = STATE_SUDDEN_DEATH
            else:
                self.retribution_player     = player
                self.retribution_start_time = pygame.time.get_ticks()
                self.state                  = STATE_RETRIBUTION

    def undo(self):
        if not self.score_history:
            return
        last = self.score_history.pop()
        if last['player'] == 1: self.player1_score = last['prev']
        else:                   self.player2_score = last['prev']
        self.winner      = None
        self.state       = STATE_PLAYING
        self.game_active = True

# ---------------------------------------------------------------------------
# Draw helpers
# ---------------------------------------------------------------------------
def winner_text_color(pt):
    return (int(127 + 127 * math.sin(pt * 3)),
            int(127 + 127 * math.sin(pt * 3 + 2)),
            int(127 + 127 * math.sin(pt * 3 + 4)))

def pulse_brightness(pt):
    return 1.2 + 0.4 * abs(math.sin(pt * 2))

def draw_glow(surface, text, font, color, cx, cy, glow_color, passes=4):
    """Fast glow: render twice, blit 8 offset copies for halo, no Surface allocs."""
    ts = font.render(text, True, color)
    tr = ts.get_rect(center=(cx, cy))
    gs = font.render(text, True, glow_color)
    gs.set_alpha(80)
    for dx, dy in ((-passes,0),(passes,0),(0,-passes),(0,passes),
                   (-passes,-passes),(passes,passes),(-passes,passes),(passes,-passes)):
        surface.blit(gs, (tr.x + dx, tr.y + dy))
    surface.blit(ts, tr)

def draw_overlay():
    screen.blit(_overlay_surf, (0, 0))

def bc(surf, cx, cy):   # blit centered
    screen.blit(surf, surf.get_rect(center=(cx, cy)))

def draw_panel(ps, px, py, pw, ph, border=WHITE):
    screen.blit(ps, (px, py))
    pygame.draw.rect(screen, border, pygame.Rect(px, py, pw, ph), width=3, border_radius=8)

def draw_strip(strip_s, px, ry, pw, rh, border_col=(120, 120, 120)):
    sr = pygame.Rect(px + 3, ry, pw - 6, rh)
    screen.blit(strip_s, sr)
    pygame.draw.rect(screen, border_col, sr, width=2, border_radius=5)

def divider(px, dy, pw):
    pygame.draw.line(screen, (140, 145, 155), (px + 20, dy), (px + pw - 20, dy), 1)

# Winner font cache — avoid recreating the font when scale hasn't changed
_wf_sz  = [0]
_wf_obj = [pygame.font.Font(None, 110)]

def get_winner_font(sz):
    sz = max(40, sz)
    if sz != _wf_sz[0]:
        _wf_obj[0] = pygame.font.Font(None, sz)
        _wf_sz[0]  = sz
    return _wf_obj[0]

# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------
def draw_scoreboard(game, now):
    pt = game.pulse_time

    if game.winner == 1:
        br = pulse_brightness(pt)
        p1 = tuple(min(255, int(c * br)) for c in BLUE)
        p2 = GREY
    elif game.winner == 2:
        br = pulse_brightness(pt)
        p1 = GREY
        p2 = tuple(min(255, int(c * br)) for c in RED)
    else:
        p1, p2 = BLUE, RED

    pygame.draw.rect(screen, p1, (0,          header_height, half_width, scoreboard_height))
    pygame.draw.rect(screen, p2, (half_width, header_height, half_width, scoreboard_height))

    if   game.winner == 2: screen.blit(_grey_half, (0,          header_height))
    elif game.winner == 1: screen.blit(_grey_half, (half_width, header_height))

    pygame.draw.line(screen, BLACK,
                     (half_width, header_height), (half_width, height - footer_height), 4)

    wcol = winner_text_color(pt)

    if game.winner in (1, 2):
        t     = now - game.winner_announced_time
        scale = (1.0 + 0.5 * (t / 500)) if t < 500 else (1.5 + abs(math.sin((t - 500) / 200)) * 0.3)
        sz    = min(int(110 * scale), int(half_width * 1.4))
        cx    = half_width // 2 if game.winner == 1 else half_width + half_width // 2
        draw_glow(screen, "WINNER", get_winner_font(sz), wcol,
                  cx, score_center_y - 230, YELLOW, passes=4)

    s1 = get_score_surf(game.player1_score)
    s2 = get_score_surf(game.player2_score)
    screen.blit(s1, s1.get_rect(center=(half_width // 2,               score_center_y)))
    screen.blit(s2, s2.get_rect(center=(half_width + half_width // 2,  score_center_y)))

    pygame.draw.rect(screen, DARK_GREY, (0,     0,                   width, header_height))
    pygame.draw.rect(screen, DARK_GREY, (0, height - footer_height,  width, footer_height))

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    game    = GameState()
    clock   = pygame.time.Clock()
    running = True
    FPS     = 30          # 30 fps — halves CPU vs 60, plenty for a scoreboard
    OVER21_MS = 2000

    while running:
        now = pygame.time.get_ticks()
        dt  = clock.tick(FPS)
        game.pulse_time += dt / 1000.0
        pt = game.pulse_time

        # ------------------------------------------------------------------ #
        #  Events                                                              #
        # ------------------------------------------------------------------ #
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.JOYBUTTONDOWN:
                joy, btn = event.joy, event.button

                # ---- Quit trigger (always available) ----
                if joy == 2 and btn == 9:
                    game.pre_quit_state = game.state
                    game.state = STATE_CONFIRM_QUIT

                # ---- Enter Edit Score ----
                elif joy == 2 and btn == 5 and game.state in (
                        STATE_PLAYING, STATE_RETRIBUTION_WAIT, STATE_SUDDEN_DEATH):
                    game.edit_player = 1; game.pre_edit_state = game.state
                    game.state = STATE_EDIT_SCORE

                elif joy == 2 and btn == 6 and game.state in (
                        STATE_PLAYING, STATE_RETRIBUTION_WAIT, STATE_SUDDEN_DEATH):
                    game.edit_player = 2; game.pre_edit_state = game.state
                    game.state = STATE_EDIT_SCORE

                # ---- Edit Score controls ----
                elif game.state == STATE_EDIT_SCORE:
                    if   joy == 2 and btn == 4:   # Black = +1
                        if game.edit_player == 1: game.player1_score += 1
                        else:                     game.player2_score += 1
                    elif joy == 2 and btn == 8:   # White = -1
                        if game.edit_player == 1: game.player1_score = max(0, game.player1_score - 1)
                        else:                     game.player2_score = max(0, game.player2_score - 1)
                    elif joy == 2 and btn == 5:   # P1 = Done
                        game.state = game.pre_edit_state
                        game.edit_player = None; game.pre_edit_state = None
                    elif joy == 2 and btn == 7:   # Blue = Skeech
                        game.state = STATE_SKEECH_CONFIRM
                    # all other buttons do nothing

                # ---- Skeech confirm ----
                elif game.state == STATE_SKEECH_CONFIRM:
                    if joy == 2 and btn == 7:     # Blue = confirm
                        sw = game.edit_player
                        game.winner = sw; game.skeech_winner = sw
                        game.game_active = False; game.winner_announced_time = now
                        game.edit_player = None; game.pre_edit_state = None
                        game.state = STATE_WINNER
                    elif joy == 2 and btn == 8:   # White = cancel
                        game.state = STATE_EDIT_SCORE

                # ---- Confirm Quit / Exit dialog ----
                elif game.state == STATE_CONFIRM_QUIT:
                    if   joy == 2 and btn == 8:   # White = back to menu
                        game.go_to_welcome()
                    elif joy == 2 and btn == 4:   # Black = cancel
                        game.state = game.pre_quit_state
                    elif joy == 1 and btn == 2:   # Red = kill app completely
                        pygame.quit()
                        sys.exit()

                # ---- Declare Winner dialog ----
                elif game.state == STATE_DECLARE_WINNER:
                    if   joy == 2 and btn == 4:   # Black = confirm
                        game.winner = game.declare_winner_player
                        game.game_active = False; game.winner_announced_time = now
                        game.declare_winner_player = None; game.state = STATE_WINNER
                    elif joy == 2 and btn == 8:   # White = cancel
                        game.state = game.pre_declare_state
                        game.declare_winner_player = None
                    elif joy == 2 and btn == 7:   # Blue = Skeech
                        # player attempting retribution (opponent of retribution_player) wins
                        if game.retribution_player is not None:
                            sw = 2 if game.retribution_player == 1 else 1
                        else:
                            sw = game.declare_winner_player
                        game.winner = sw; game.skeech_winner = sw
                        game.game_active = False; game.winner_announced_time = now
                        game.declare_winner_player = None; game.state = STATE_WINNER

                # ---- Start game ----
                elif joy == 2 and btn == 3:
                    game.start_game()

                # ---- Retribution dialog ----
                elif game.state == STATE_RETRIBUTION:
                    if   joy == 2 and btn == 8:   # White = game over, first player wins
                        game.winner = game.retribution_player
                        game.game_active = False; game.winner_announced_time = now
                        game.state = STATE_WINNER
                    elif joy == 2 and btn == 4:   # Black = allow retribution attempt
                        game.state = STATE_RETRIBUTION_WAIT; game.game_active = True

                # ---- Retribution Wait ----
                elif game.state == STATE_RETRIBUTION_WAIT:
                    if joy == 2 and btn == 4:
                        game.declare_winner_player = game.retribution_player
                        game.pre_declare_state = STATE_RETRIBUTION_WAIT
                        game.state = STATE_DECLARE_WINNER
                    elif joy == 0 and btn == 0:   game.add_score(1, 1)
                    elif joy == 0 and btn == 1:   game.add_score(1, 3)
                    elif joy == 0 and btn == 2:   game.add_score(1, 5)
                    elif joy == 0 and btn == 10:  game.add_score(1, 3)
                    elif joy == 0 and btn == 11:  game.add_score(1, 1)
                    elif joy == 1 and btn == 0:   game.add_score(2, 1)
                    elif joy == 1 and btn == 1:   game.add_score(2, 3)
                    elif joy == 1 and btn == 2:   game.add_score(2, 5)
                    elif joy == 1 and btn == 10:  game.add_score(2, 3)
                    elif joy == 1 and btn == 11:  game.add_score(2, 1)

                # ---- Sudden Death ----
                elif game.state == STATE_SUDDEN_DEATH:
                    if joy == 2 and btn == 4:
                        leading = 1 if game.player1_score >= game.player2_score else 2
                        game.declare_winner_player = leading
                        game.pre_declare_state = STATE_SUDDEN_DEATH
                        game.state = STATE_DECLARE_WINNER

                # ---- Normal gameplay ----
                elif game.state == STATE_PLAYING:
                    if   joy == 0 and btn == 0:   game.add_score(1, 1)
                    elif joy == 0 and btn == 1:   game.add_score(1, 3)
                    elif joy == 0 and btn == 2:   game.add_score(1, 5)
                    elif joy == 0 and btn == 10:  game.add_score(1, 3)
                    elif joy == 0 and btn == 11:  game.add_score(1, 1)
                    elif joy == 1 and btn == 0:   game.add_score(2, 1)
                    elif joy == 1 and btn == 1:   game.add_score(2, 3)
                    elif joy == 1 and btn == 2:   game.add_score(2, 5)
                    elif joy == 1 and btn == 10:  game.add_score(2, 3)
                    elif joy == 1 and btn == 11:  game.add_score(2, 1)

            elif event.type == pygame.KEYDOWN:
                key = event.key
                if key == pygame.K_ESCAPE:
                    game.pre_quit_state = game.state; game.state = STATE_CONFIRM_QUIT
                elif game.state == STATE_CONFIRM_QUIT:
                    if   key == pygame.K_y: game.go_to_welcome()
                    elif key == pygame.K_n: game.state = game.pre_quit_state
                    elif key == pygame.K_k: pygame.quit(); sys.exit()
                elif key == pygame.K_SPACE:     game.start_game()
                elif key == pygame.K_BACKSPACE: game.undo()
                elif game.state == STATE_DECLARE_WINNER:
                    if   key == pygame.K_RETURN:
                        game.winner = game.declare_winner_player; game.game_active = False
                        game.winner_announced_time = now; game.declare_winner_player = None
                        game.state = STATE_WINNER
                    elif key == pygame.K_x:
                        game.state = game.pre_declare_state; game.declare_winner_player = None
                elif game.state == STATE_RETRIBUTION:
                    if   key == pygame.K_n:
                        game.winner = game.retribution_player; game.game_active = False
                        game.winner_announced_time = now; game.state = STATE_WINNER
                    elif key == pygame.K_y:
                        game.state = STATE_RETRIBUTION_WAIT; game.game_active = True
                elif game.state == STATE_RETRIBUTION_WAIT:
                    if   key == pygame.K_d:
                        game.declare_winner_player = game.retribution_player
                        game.pre_declare_state = STATE_RETRIBUTION_WAIT; game.state = STATE_DECLARE_WINNER
                    elif key == pygame.K_q: game.add_score(1, 1)
                    elif key == pygame.K_w: game.add_score(1, 3)
                    elif key == pygame.K_e: game.add_score(1, 5)
                    elif key == pygame.K_i: game.add_score(2, 1)
                    elif key == pygame.K_o: game.add_score(2, 3)
                    elif key == pygame.K_p: game.add_score(2, 5)
                elif game.state == STATE_SUDDEN_DEATH:
                    if key == pygame.K_d:
                        leading = 1 if game.player1_score >= game.player2_score else 2
                        game.declare_winner_player = leading
                        game.pre_declare_state = STATE_SUDDEN_DEATH; game.state = STATE_DECLARE_WINNER
                elif game.state == STATE_PLAYING:
                    if   key == pygame.K_q: game.add_score(1, 1)
                    elif key == pygame.K_w: game.add_score(1, 3)
                    elif key == pygame.K_e: game.add_score(1, 5)
                    elif key == pygame.K_i: game.add_score(2, 1)
                    elif key == pygame.K_o: game.add_score(2, 3)
                    elif key == pygame.K_p: game.add_score(2, 5)

        # ------------------------------------------------------------------ #
        #  Auto-transitions                                                    #
        # ------------------------------------------------------------------ #
        if game.state == STATE_OVER_21 and now - game.over21_start_time >= OVER21_MS:
            game.state = STATE_PLAYING; game.over21_player = None; game.over21_start_time = None

        if game.state == STATE_SUDDEN_DEATH and now - game.sudden_death_start_time >= 5000:
            game.player1_score = 0; game.player2_score = 0
            game.retribution_player = None; game.state = STATE_PLAYING

        # ------------------------------------------------------------------ #
        #  Render                                                              #
        # ------------------------------------------------------------------ #
        screen.fill(BLACK)

        # ===== WELCOME =====
        if game.state == STATE_WELCOME:
            draw_glow(screen, "SKEECH", title_mega_font, WHITE,
                      width // 2, height // 2 - 100, YELLOW, passes=4)
            surf_press_start_play.set_alpha(int(200 + 55 * math.sin(pt * 3)))
            bc(surf_press_start_play, width // 2, height // 2 + 150)
            pygame.display.flip()
            continue

        # ===== SCOREBOARD BASE =====
        draw_scoreboard(game, now)

        # ===== STATE OVERLAYS =====
        cx = width // 2

        if game.state == STATE_OVER_21:
            draw_overlay()
            surf_over21.set_alpha(int(180 + 75 * math.sin((now - game.over21_start_time) / 120.0)))
            bc(surf_over21, cx, height // 2 - 60)

        elif game.state == STATE_RETRIBUTION:
            draw_overlay()
            surf_ret_title.set_alpha(int(200 + 55 * math.sin(pt * 4)))
            bc(surf_ret_title, cx, height // 2 - 130)

            draw_panel(_ret_panel_s, _ret_panel_x, _ret_panel_y, _ret_panel_w, _ret_panel_h)
            row1_y = _ret_panel_y + _PAD_Y
            bc(surf_white_gameover, cx, row1_y + _ret_row_h // 2)
            div_y = row1_y + _ret_row_h + _ROW_GAP // 2
            divider(_ret_panel_x, div_y, _ret_panel_w)
            row2_y = div_y + _ROW_GAP // 2
            draw_strip(_ret_strip, _ret_panel_x, row2_y, _ret_panel_w, _ret_row_h)
            bc(surf_black_retrib, cx, row2_y + _ret_row_h // 2)

        elif game.state == STATE_RETRIBUTION_WAIT:
            surf_declare_banner_rw.set_alpha(int(160 + 75 * math.sin(pt * 2.5 + 1)))
            drect = surf_declare_banner_rw.get_rect(center=(cx, height - footer_height - 30))
            screen.blit(_bg_declare_rw, _bg_declare_rw.get_rect(center=drect.center))
            screen.blit(surf_declare_banner_rw, drect)

        elif game.state == STATE_SUDDEN_DEATH:
            elapsed = now - game.sudden_death_start_time
            draw_overlay()
            sd_col = winner_text_color(pt)
            sd_s   = sd_font.render("SUDDEN DEATH!", True, sd_col)
            sd_s.set_alpha(int(160 + 95 * math.sin(elapsed / 150.0)))
            bc(sd_s, cx, height // 2 - 60)
            surf_declare_banner_sd.set_alpha(int(180 + 75 * math.sin(pt * 2.5)))
            drect = surf_declare_banner_sd.get_rect(center=(cx, height - footer_height - 40))
            screen.blit(_bg_declare_sd, _bg_declare_sd.get_rect(center=drect.center))
            screen.blit(surf_declare_banner_sd, drect)

        elif game.state == STATE_DECLARE_WINNER:
            draw_overlay()
            pname = "Blue" if game.declare_winner_player == 1 else "Red"
            pcol  = BLUE   if game.declare_winner_player == 1 else RED
            dw_s  = dw_font.render(f"Declare {pname} Winner?", True, pcol)
            dw_s.set_alpha(int(200 + 55 * math.sin(pt * 4)))
            bc(dw_s, cx, height // 2 - 110)

            draw_panel(_dw_panel_s, _dw_panel_x, _dw_panel_y, _dw_panel_w, _dw_panel_h)
            row1_y = _dw_panel_y + _PAD_Y
            draw_strip(_dw_strip1, _dw_panel_x, row1_y, _dw_panel_w, _dw_row_h)
            bc(surf_dw_confirm, cx, row1_y + _dw_row_h // 2)
            div1_y = row1_y + _dw_row_h + _ROW_GAP // 2
            divider(_dw_panel_x, div1_y, _dw_panel_w)
            row2_y = div1_y + _ROW_GAP // 2
            bc(surf_dw_cancel, cx, row2_y + _dw_row_h // 2)
            div2_y = row2_y + _dw_row_h + _ROW_GAP // 2
            divider(_dw_panel_x, div2_y, _dw_panel_w)
            row3_y = div2_y + _ROW_GAP // 2
            draw_strip(_dw_bstrip, _dw_panel_x, row3_y, _dw_panel_w, _dw_row_h, border_col=BLUE)
            bc(surf_dw_skeech, cx, row3_y + _dw_row_h // 2)

        elif game.state == STATE_WINNER:
            surf_press_again.set_alpha(int(200 + 55 * math.sin(pt * 3)))
            pygame.draw.rect(screen, BLACK,  _psa_box)
            pygame.draw.rect(screen, YELLOW, _psa_box, 3)
            screen.blit(surf_press_again, _psa_rect)
            if game.skeech_winner is not None:
                lx = (half_width + half_width // 2) if game.skeech_winner == 1 else half_width // 2
                surf_skeeched.set_alpha(int(200 + 55 * math.sin(pt * 3.5)))
                bc(surf_skeeched, lx, score_center_y + 200)

        elif game.state in (STATE_EDIT_SCORE, STATE_SKEECH_CONFIRM):
            edit_p = game.edit_player
            screen.blit(_edit_grey, (half_width if edit_p == 1 else 0, header_height))

            bsrf = surf_edit_blue_banner if edit_p == 1 else surf_edit_red_banner
            screen.blit(_banner_bg, _banner_bg.get_rect(center=(cx, header_height + 40)))
            bc(bsrf, cx, header_height + 40)

            screen.blit(_bar_bg, (0, _bar_y))
            pygame.draw.rect(screen, GREY, pygame.Rect(0, _bar_y, width, _bar_h), 2)
            lbls = [surf_edit_black_lbl, surf_edit_white_lbl, surf_edit_p1_lbl, surf_edit_blue_lbl]
            for i, (seg_s, lbl_s) in enumerate(zip(_seg_surfs, lbls)):
                sx = i * _seg_w
                screen.blit(seg_s, (sx + 2, _bar_y + 2))
                bc(lbl_s, sx + _seg_w // 2, _bar_y + _bar_h // 2)

            if game.state == STATE_SKEECH_CONFIRM:
                ec = BLUE if edit_p == 1 else RED
                ts = surf_sc_blue_title if edit_p == 1 else surf_sc_red_title
                screen.blit(_sc_pop_s, (_sc_pop_x, _sc_pop_y))
                pygame.draw.rect(screen, ec,
                                 pygame.Rect(_sc_pop_x, _sc_pop_y, _sc_pop_w, _sc_pop_h),
                                 3, border_radius=10)
                bc(ts, cx, _sc_pop_y + 75)
                cur_x  = cx - SC_SUBLINE_W // 2
                sub_y  = _sc_pop_y + 165
                for s in (surf_sc_press, surf_sc_blue, surf_sc_confirm,
                          surf_sc_white_word, surf_sc_cancel):
                    screen.blit(s, (cur_x, sub_y))
                    cur_x += s.get_width()

        # ---- Confirm Quit / Exit — always drawn on top ----
        if game.state == STATE_CONFIRM_QUIT:
            draw_overlay()
            surf_quit_title.set_alpha(int(200 + 55 * math.sin(pt * 4)))
            bc(surf_quit_title, cx, height // 2 - 120)

            draw_panel(_quit_panel_s, _quit_panel_x, _quit_panel_y, _quit_panel_w, _quit_panel_h)
            row1_y = _quit_panel_y + _PAD_Y
            bc(surf_quit_yes, cx, row1_y + _quit_row_h // 2)
            div1_y = row1_y + _quit_row_h + _ROW_GAP // 2
            divider(_quit_panel_x, div1_y, _quit_panel_w)
            row2_y = div1_y + _ROW_GAP // 2
            draw_strip(_quit_strip_no, _quit_panel_x, row2_y, _quit_panel_w, _quit_row_h)
            bc(surf_quit_no, cx, row2_y + _quit_row_h // 2)
            div2_y = row2_y + _quit_row_h + _ROW_GAP // 2
            divider(_quit_panel_x, div2_y, _quit_panel_w)
            row3_y = div2_y + _ROW_GAP // 2
            draw_strip(_quit_strip_kill, _quit_panel_x, row3_y, _quit_panel_w, _quit_row_h,
                       border_col=RED)
            bc(surf_quit_kill, cx, row3_y + _quit_row_h // 2)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()