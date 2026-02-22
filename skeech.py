#!/usr/bin/env python3
"""
Two-Player Scoreboard Application
For Raspberry Pi 3 with keyboard input
"""

import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
if pygame.joystick.get_count() > 1:
        joystick2 = pygame.joystick.Joystick(1)
        joystick2.init()
if pygame.joystick.get_count() > 2:
        joystick3= pygame.joystick.Joystick(2)
        joystick3.init()

# Screen setup
screen = pygame.display.set_mode((1200, 800))
pygame.display.set_caption("Scoreboard")
width, height = screen.get_size()

# Colors
BLUE      = (37, 99, 235)
RED       = (220, 38, 38)
GREY      = (75, 85, 99)
DARK_GREY = (45, 45, 45)
YELLOW    = (251, 191, 36)
GREEN     = (52, 211, 153)
WHITE     = (255, 255, 255)
BLACK     = (26, 26, 26)
ORANGE    = (255, 140, 0)

# Fonts
title_font    = pygame.font.Font(None, 60)
score_font    = pygame.font.Font(None, 500)
winner_font   = pygame.font.Font(None, 150)
controls_font = pygame.font.Font(None, 40)
footer_font   = pygame.font.Font(None, 35)

# ---------------------------------------------------------------------------
# Confetti
# ---------------------------------------------------------------------------
class Confetti:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-15, -5)
        self.gravity = 0.5
        self.color = random.choice([YELLOW, GREEN, (255,100,100), (100,100,255), (255,150,0)])
        self.size = random.randint(5, 12)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-10, 10)

    def update(self):
        self.vy += self.gravity
        self.x  += self.vx
        self.y  += self.vy
        self.rotation += self.rotation_speed

    def draw(self, surface):
        points = []
        for i in range(4):
            angle = math.radians(self.rotation + i * 90)
            points.append((self.x + math.cos(angle) * self.size,
                           self.y + math.sin(angle) * self.size))
        pygame.draw.polygon(surface, self.color, points)

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
STATE_CONFIRM_RESTART  = "confirm_restart"
STATE_CONFIRM_QUIT     = "confirm_quit"
STATE_EDIT_SCORE       = "edit_score"

# ---------------------------------------------------------------------------
# GameState
# ---------------------------------------------------------------------------
class GameState:
    def __init__(self):
        self.player1_score       = 0
        self.player2_score       = 0
        self.game_active         = False
        self.winner              = None
        self.score_history       = []
        self.pulse_time          = 0
        self.confetti            = []
        self.winner_announced_time = None
        self.show_welcome        = True
        self.state               = STATE_WELCOME
        self.over21_player       = None
        self.over21_start_time   = None
        self.retribution_player  = None
        self.retribution_start_time = None
        self.sudden_death_start_time = None
        self.pre_confirm_state   = None   # state to restore on cancel
        self.edit_player            = None   # 1 or 2
        self.pre_edit_state         = None   # state to restore when done editing


    def start_game(self):
        self.player1_score          = 0
        self.player2_score          = 0
        self.game_active            = True
        self.winner                 = None
        self.score_history          = []
        self.confetti               = []
        self.winner_announced_time  = None
        self.show_welcome           = False
        self.state                  = STATE_PLAYING
        self.over21_player          = None
        self.over21_start_time      = None
        self.retribution_player     = None
        self.retribution_start_time = None
        self.sudden_death_start_time = None
        self.pre_confirm_state      = None

    def go_to_welcome(self):
        """Reset everything and return to welcome screen."""
        self.__init__()
    
    # Enter edit-score mode; save the current state so we can restore it
    def enter_edit_score(self, player):
        self.edit_player     = player
        self.pre_edit_state  = self.state
        self.state           = STATE_EDIT_SCORE

    # Leave edit-score mode and restore previous state
    def exit_edit_score(self):
        self.state       = self.pre_edit_state
        self.edit_player = None

    def edit_adjust(self, delta):
        """Add or subtract a point from the player being edited (clamped to 0)."""
        if self.edit_player == 1:
            self.player1_score = max(0, self.player1_score + delta)
        else:
            self.player2_score = max(0, self.player2_score + delta)


    def add_score(self, player, points):
        if self.state not in (STATE_PLAYING, STATE_RETRIBUTION_WAIT):
            return
        if player == 1:
            self.score_history.append({'player': 1, 'prev_score': self.player1_score, 'points': points})
            self.player1_score += points
        else:
            self.score_history.append({'player': 2, 'prev_score': self.player2_score, 'points': points})
            self.player2_score += points
        self.check_score(player)

    def check_score(self, player):
        score = self.player1_score if player == 1 else self.player2_score
        if score > 21:
            if player == 1:
                self.player1_score = 15
            else:
                self.player2_score = 15
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
        if last['player'] == 1:
            self.player1_score = last['prev_score']
        else:
            self.player2_score = last['prev_score']
        self.winner      = None
        self.state       = STATE_PLAYING
        self.game_active = True

    def spawn_confetti(self):
        for _ in range(100):
            self.confetti.append(Confetti(random.randint(0, width), random.randint(-100, height // 3)))

    def update_confetti(self):
        for c in self.confetti[:]:
            c.update()
            if c.y > height + 50:
                self.confetti.remove(c)

# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def get_winner_text_scale(time_since_win):
    if time_since_win < 500:
        return 1.0 + 0.5 * (time_since_win / 500)
    bounce = abs(math.sin((time_since_win - 500) / 200))
    return 1.5 + bounce * 0.3

def get_winner_text_color(pulse_time):
    return (int(127 + 127 * math.sin(pulse_time * 3)),
            int(127 + 127 * math.sin(pulse_time * 3 + 2)),
            int(127 + 127 * math.sin(pulse_time * 3 + 4)))

def draw_text_centered(surface, text, font, color, x, y):
    s = font.render(text, True, color)
    surface.blit(s, s.get_rect(center=(x, y)))

def draw_glow_text(surface, text, font, color, x, y, glow_color, glow_amount=8):
    text_surface = font.render(text, True, color)
    text_rect    = text_surface.get_rect(center=(x, y))
    for offset in range(glow_amount, 0, -1):
        alpha     = 255 - (offset * 255 // glow_amount)
        glow_size = offset * 2
        gs        = pygame.Surface((text_surface.get_width()  + glow_size * 2,
                                    text_surface.get_height() + glow_size * 2), pygame.SRCALPHA)
        gt = font.render(text, True, glow_color)
        gt.set_alpha(alpha)
        gs.blit(gt, gt.get_rect(center=(gs.get_width() // 2, gs.get_height() // 2)))
        surface.blit(gs, gs.get_rect(center=(x, y)))
    surface.blit(text_surface, text_rect)

def get_pulse_brightness(pulse_time):
    return 1.2 + 0.4 * abs(math.sin(pulse_time * 2))

def draw_overlay_box(surface, w, h, bg_color=(20, 20, 20), alpha=220):
    ov = pygame.Surface((w, h), pygame.SRCALPHA)
    ov.fill((*bg_color, alpha))
    surface.blit(ov, (0, 0))

def draw_scoreboard(screen, game, width, height, hh, fh, sbh, hw):
    """Draw background panels, winner label, and scores."""
    if game.winner == 1:
        p1c = tuple(min(255, int(c * get_pulse_brightness(game.pulse_time))) for c in BLUE)
        p2c = GREY
    elif game.winner == 2:
        p1c = GREY
        p2c = tuple(min(255, int(c * get_pulse_brightness(game.pulse_time))) for c in RED)
    else:
        p1c, p2c = BLUE, RED

    pygame.draw.rect(screen, p1c, (0,  hh, hw,  sbh))
    pygame.draw.rect(screen, p2c, (hw, hh, hw,  sbh))

    if game.winner == 2:
        ov = pygame.Surface((hw, sbh)); ov.set_alpha(128); ov.fill(GREY)
        screen.blit(ov, (0, hh))
    elif game.winner == 1:
        ov = pygame.Surface((hw, sbh)); ov.set_alpha(128); ov.fill(GREY)
        screen.blit(ov, (hw, hh))

    # Edit-score mode: grey out the non-edited side
    if game.state == STATE_EDIT_SCORE:
        if game.edit_player == 1:
            ov = pygame.Surface((hw, sbh)); ov.set_alpha(160); ov.fill(GREY)
            screen.blit(ov, (hw, hh))
        else:
            ov = pygame.Surface((hw, sbh)); ov.set_alpha(160); ov.fill(GREY)
            screen.blit(ov, (0, hh))

    pygame.draw.line(screen, BLACK, (hw, hh), (hw, height - fh), 4)

    if game.winner == 1:
        tsw   = pygame.time.get_ticks() - game.winner_announced_time
        sc    = get_winner_text_scale(tsw)
        wc    = get_winner_text_color(game.pulse_time)
        sfont = pygame.font.Font(None, int(150 * sc))
        draw_glow_text(screen, "WINNER", sfont, wc, hw // 2, hh + 220, YELLOW, glow_amount=8)

    draw_text_centered(screen, str(game.player1_score), score_font, WHITE, hw // 2, hh + sbh // 2)

    if game.winner == 2:
        tsw   = pygame.time.get_ticks() - game.winner_announced_time
        sc    = get_winner_text_scale(tsw)
        wc    = get_winner_text_color(game.pulse_time)
        sfont = pygame.font.Font(None, int(150 * sc))
        draw_glow_text(screen, "WINNER", sfont, wc, hw + hw // 2, hh + 220, YELLOW, glow_amount=8)

    draw_text_centered(screen, str(game.player2_score), score_font, WHITE, hw + hw // 2, hh + sbh // 2)

    pygame.draw.rect(screen, DARK_GREY, (0, 0,            width, hh))
    pygame.draw.rect(screen, DARK_GREY, (0, height - fh,  width, fh))


def draw_confirm_dialog(screen, width, height, title_text, btn_font, sub_font, pulse_time):
    """Generic Yes / No confirmation overlay."""
    draw_overlay_box(screen, width, height)
    conf_font   = pygame.font.Font(None, 110)
    pulse_alpha = int(200 + 55 * math.sin(pulse_time * 4))

    ts = conf_font.render(title_text, True, YELLOW)
    ts.set_alpha(pulse_alpha)
    screen.blit(ts, ts.get_rect(center=(width // 2, height // 2 - 90)))

    hint = sub_font.render("START = Yes        SELECT = No", True, WHITE)
    screen.blit(hint, hint.get_rect(center=(width // 2, height // 2 + 10)))

    # NO button (left)
    no_rect  = pygame.Rect(width // 2 - 290, height // 2 + 100, 240, 90)
    pygame.draw.rect(screen, RED, no_rect, border_radius=12)
    ns = btn_font.render("NO  (N)", True, WHITE)
    screen.blit(ns, ns.get_rect(center=no_rect.center))

    # YES button (right)
    yes_rect = pygame.Rect(width // 2 + 50, height // 2 + 100, 240, 90)
    pygame.draw.rect(screen, GREEN, yes_rect, border_radius=12)
    ys = btn_font.render("YES  (Y)", True, WHITE)
    screen.blit(ys, ys.get_rect(center=yes_rect.center))

def draw_edit_score_overlay(screen, game, width, height, hh, fh, btn_font, sub_font):
    """Draw the edit-score UI elements on top of the scoreboard."""
    player_name  = "Blue" if game.edit_player == 1 else "Red"
    label_color  = BLUE   if game.edit_player == 1 else RED

    # Title banner at top of the edited side
    hw = width // 2
    ef = pygame.font.Font(None, 90)
    et = ef.render(f"Edit {player_name} Score", True, WHITE)
    # Draw coloured pill behind it on the active side
    ex = hw//2 if game.edit_player == 1 else hw + hw//2
    pill_w, pill_h = et.get_width()+40, et.get_height()+20
    pill = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
    pill.fill((*label_color, 200))
    screen.blit(pill, pill.get_rect(center=(ex, hh+80)))
    screen.blit(et, et.get_rect(center=(ex, hh+80)))

    # White (+1) and Black (-1) button hints above the score
    wf = pygame.font.Font(None, 60)
    plus_s  = wf.render("WHITE = +1", True, WHITE)
    minus_s = wf.render("BLACK = -1", True, (180,180,180))
    screen.blit(plus_s,  plus_s.get_rect(center=(ex, hh+160)))
    screen.blit(minus_s, minus_s.get_rect(center=(ex, hh+220)))

    # "Press Blue to Resume" at the bottom
    rf = pygame.font.Font(None, 65)
    resume_s = rf.render("Press Blue to Resume", True, BLUE)
    pa = int(200 + 55*math.sin(pygame.time.get_ticks()/300.0))
    resume_s.set_alpha(pa)
    rb = resume_s.get_rect(center=(width//2, height - fh - 40))
    bg_surf = pygame.Surface((rb.width+40, rb.height+20), pygame.SRCALPHA)
    bg_surf.fill((0,0,0,160))
    screen.blit(bg_surf, bg_surf.get_rect(center=rb.center))
    screen.blit(resume_s, rb)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    game    = GameState()
    clock   = pygame.time.Clock()
    running = True

    hh  = 20                            # header height
    fh  = 20                            # footer height
    sbh = height - hh - fh             # scoreboard height
    hw  = width // 2

    sub_font = pygame.font.Font(None, 70)
    btn_font = pygame.font.Font(None, 80)

    OVER21_DISPLAY_MS = 2000
    
    # States where edit-score can be entered
    EDITABLE_STATES = (STATE_PLAYING, STATE_RETRIBUTION_WAIT,
                       STATE_RETRIBUTION, STATE_OVER_21, STATE_SUDDEN_DEATH)

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ----------------------------------------------------------------
            elif event.type == pygame.JOYBUTTONDOWN:
                print(f"Joystick {event.joy} Button {event.button} pressed")
                j, b = event.joy, event.button

                # ---- Confirm Restart ----
                if game.state == STATE_CONFIRM_RESTART:
                    if j == 2 and b == 0:          # START → yes, restart
                        game.start_game()
                    elif j == 2 and b == 5:        # SELECT → no, cancel
                        game.state = game.pre_confirm_state

                # ---- Confirm Quit ----
                elif game.state == STATE_CONFIRM_QUIT:
                    if j == 2 and b == 0:          # START → yes, go to welcome
                        game.go_to_welcome()
                    elif j == 2 and b == 5:        # SELECT → no, cancel
                        game.state = game.pre_confirm_state
                
                # ==== Edit Score mode ====
                elif game.state == STATE_EDIT_SCORE:
                    if j == 2 and b == 5:           # White button → +1
                        game.edit_adjust(+1)
                    elif j == 2 and b == 1:         # Black button → -1
                        game.edit_adjust(-1)
                    elif j == 2 and b == 4:         # Blue button → resume
                        game.exit_edit_score()


                # ---- Meta buttons (START / QUIT) outside dialogs ----
                elif j == 2 and b == 6:            # QUIT button
                    if game.state == STATE_WELCOME:
                        running = False
                    else:
                        game.pre_confirm_state = game.state
                        game.state = STATE_CONFIRM_QUIT

                elif j == 2 and b == 0:            # START button
                    if game.state == STATE_WELCOME:
                        game.start_game()
                    else:
                        # Mid-game or winner screen: ask to confirm restart
                        game.pre_confirm_state = game.state
                        game.state = STATE_CONFIRM_RESTART

                # ---- Winner screen: SELECT = back to menu ----
                elif game.state == STATE_WINNER and j == 2 and b == 5:
                    game.go_to_welcome()
                
                # ==== Edit Score entry buttons (joy2 btn2 = Blue, btn3 = Red) ====
                elif j == 2 and b == 2 and game.state in EDITABLE_STATES:
                    game.enter_edit_score(1)   # Blue = Player 1

                elif j == 2 and b == 3 and game.state in EDITABLE_STATES:
                    game.enter_edit_score(2)   # Red  = Player 2


                # ---- Retribution: joy2 btn5 = No (winner), btn1 = Yes (continue) ----
                elif game.state == STATE_RETRIBUTION:
                    if j == 2 and b == 5:
                        game.winner = game.retribution_player
                        game.game_active = False
                        game.winner_announced_time = now
                        game.state = STATE_WINNER
                    elif j == 2 and b == 1:
                        game.state = STATE_RETRIBUTION_WAIT
                        game.game_active = True

                # ---- Normal scoring ----
                elif game.state in (STATE_PLAYING, STATE_RETRIBUTION_WAIT):
                    if   j == 0 and b == 0:  game.add_score(1, 1)
                    elif j == 0 and b == 1:  game.add_score(1, 3)
                    elif j == 0 and b == 2:  game.add_score(1, 5)
                    elif j == 0 and b == 10: game.add_score(1, 3)
                    elif j == 0 and b == 11: game.add_score(1, 1)
                    elif j == 1 and b == 0:  game.add_score(2, 1)
                    elif j == 1 and b == 1:  game.add_score(2, 3)
                    elif j == 1 and b == 2:  game.add_score(2, 5)
                    elif j == 1 and b == 10: game.add_score(2, 3)
                    elif j == 1 and b == 11: game.add_score(2, 1)

            # ----------------------------------------------------------------
            elif event.type == pygame.KEYDOWN:
                k = event.key

                # ESC always triggers quit-confirm (or exits app from welcome)
                if k == pygame.K_ESCAPE:
                    if game.state == STATE_WELCOME:
                        running = False
                    elif game.state not in (STATE_CONFIRM_QUIT, STATE_CONFIRM_RESTART):
                        game.pre_confirm_state = game.state
                        game.state = STATE_CONFIRM_QUIT

                # ---- Confirm Restart ----
                elif game.state == STATE_CONFIRM_RESTART:
                    if k == pygame.K_y:
                        game.start_game()
                    elif k == pygame.K_n:
                        game.state = game.pre_confirm_state

                # ---- Confirm Quit ----
                elif game.state == STATE_CONFIRM_QUIT:
                    if k == pygame.K_y:
                        game.go_to_welcome()
                    elif k == pygame.K_n:
                        game.state = game.pre_confirm_state

                # SPACE = start / confirm restart
                elif k == pygame.K_SPACE:
                    if game.state == STATE_WELCOME:
                        game.start_game()
                    else:
                        game.pre_confirm_state = game.state
                        game.state = STATE_CONFIRM_RESTART

                elif k == pygame.K_BACKSPACE:
                    game.undo()

                # ---- Retribution keyboard ----
                elif game.state == STATE_RETRIBUTION:
                    if k == pygame.K_n:
                        game.winner = game.retribution_player
                        game.game_active = False
                        game.winner_announced_time = now
                        game.state = STATE_WINNER
                    elif k == pygame.K_y:
                        game.state = STATE_RETRIBUTION_WAIT
                        game.game_active = True

                # ---- Normal scoring keyboard ----
                elif game.state in (STATE_PLAYING, STATE_RETRIBUTION_WAIT):
                    if   k == pygame.K_q: game.add_score(1, 1)
                    elif k == pygame.K_w: game.add_score(1, 3)
                    elif k == pygame.K_e: game.add_score(1, 5)
                    elif k == pygame.K_i: game.add_score(2, 1)
                    elif k == pygame.K_o: game.add_score(2, 3)
                    elif k == pygame.K_p: game.add_score(2, 5)

        # ---- Auto-transitions ----
        if game.state == STATE_OVER_21 and now - game.over21_start_time >= OVER21_DISPLAY_MS:
            game.state = STATE_PLAYING
            game.over21_player = None
            game.over21_start_time = None

        if game.state == STATE_SUDDEN_DEATH and now - game.sudden_death_start_time >= 7000:
            game.player1_score = 0
            game.player2_score = 0
            game.retribution_player = None
            game.state = STATE_PLAYING

        game.pulse_time += clock.get_time() / 1000.0

        # ---- RENDER ----
        screen.fill(BLACK)

        # Welcome screen (no scoreboard behind it)
        if game.state == STATE_WELCOME:
            title_mega_font = pygame.font.SysFont('freeserif', 400)
            draw_glow_text(screen, "SKEECH", title_mega_font, WHITE,
                           width // 2, height // 2 - 100, YELLOW, glow_amount=10)
            pf = pygame.font.Font(None, 80)
            pa = int(200 + 55 * math.sin(game.pulse_time * 3))
            pt = pf.render("Press Start To Play", True, YELLOW)
            pt.set_alpha(pa)
            screen.blit(pt, pt.get_rect(center=(width // 2, height // 2 + 150)))
            pygame.display.flip()
            clock.tick(60)
            continue

        # Base scoreboard always drawn
        draw_scoreboard(screen, game, width, height, hh, fh, sbh, hw)

        # ---- Per-state overlays ----
        if game.state == STATE_OVER_21:
            draw_overlay_box(screen, width, height)
            elapsed = now - game.over21_start_time
            pa = int(180 + 75 * math.sin(elapsed / 120.0))
            of = pygame.font.Font(None, 140)
            os_ = of.render("You Went Over!", True, ORANGE)
            os_.set_alpha(pa)
            screen.blit(os_, os_.get_rect(center=(width // 2, height // 2 - 60)))

        elif game.state == STATE_RETRIBUTION:
            draw_overlay_box(screen, width, height)

            # Pulsing "Retribution?" title
            ret_font = pygame.font.Font(None, 160)
            pulse_alpha = int(200 + 55 * math.sin(game.pulse_time * 4))
            ret_surf = ret_font.render("Retribution?", True, YELLOW)
            ret_surf.set_alpha(pulse_alpha)
            screen.blit(ret_surf, ret_surf.get_rect(center=(width // 2, height // 2 - 130)))

            # Two message rows stacked in a grey panel
            msg_font   = pygame.font.Font(None, 62)
            white_surf = msg_font.render("White Button = Game Over",   True, WHITE)
            black_surf = msg_font.render("Black Button = Retribution", True, (20, 20, 20))

            pad_x, pad_y, row_gap = 40, 24, 14
            panel_w = max(white_surf.get_width(), black_surf.get_width()) + pad_x * 2
            panel_h = white_surf.get_height() + black_surf.get_height() + pad_y * 2 + row_gap
            panel_x = width  // 2 - panel_w // 2
            panel_y = height // 2 - 10

            # Grey background
            panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel_surf.fill((80, 85, 95, 235))
            screen.blit(panel_surf, (panel_x, panel_y))
            # White outer border
            pygame.draw.rect(screen, WHITE,
                             pygame.Rect(panel_x, panel_y, panel_w, panel_h),
                             width=3, border_radius=8)

            # Row 1: white text on grey background
            row1_y = panel_y + pad_y
            screen.blit(white_surf, white_surf.get_rect(center=(width // 2, row1_y + white_surf.get_height() // 2)))

            # Divider
            div_y = row1_y + white_surf.get_height() + row_gap // 2
            pygame.draw.line(screen, (140, 145, 155),
                             (panel_x + 20, div_y), (panel_x + panel_w - 20, div_y), 1)

            # Row 2: black text on a light strip so it's readable
            row2_y = div_y + row_gap // 2
            strip_h = black_surf.get_height() + pad_y
            strip   = pygame.Surface((panel_w - 6, strip_h), pygame.SRCALPHA)
            strip.fill((215, 215, 215, 250))
            strip_rect = pygame.Rect(panel_x + 3, row2_y, panel_w - 6, strip_h)
            screen.blit(strip, strip_rect)
            pygame.draw.rect(screen, (120, 120, 120), strip_rect, width=2, border_radius=5)
            screen.blit(black_surf, black_surf.get_rect(center=(width // 2, row2_y + strip_h // 2)))


        elif game.state == STATE_RETRIBUTION_WAIT:
            other = 2 if game.retribution_player == 1 else 1
            bf = pygame.font.Font(None, 70)
            pa = int(180 + 75 * math.sin(game.pulse_time * 3))
            bs = bf.render(f"Player {other}: Score 21 for Retribution!", True, YELLOW)
            bs.set_alpha(pa)
            br = bs.get_rect(center=(width // 2, height - fh - 50))
            bg = pygame.Surface((br.width + 36, br.height + 36), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 170))
            screen.blit(bg, br.inflate(36, 36).topleft)
            screen.blit(bs, br)

        elif game.state == STATE_SUDDEN_DEATH:
            elapsed = now - game.sudden_death_start_time
            draw_overlay_box(screen, width, height, bg_color=(0, 0, 0), alpha=200)
            sf = pygame.font.Font(None, 220)
            pa = int(160 + 95 * math.sin(elapsed / 150.0))
            sc = get_winner_text_color(game.pulse_time)
            ss = sf.render("SUDDEN DEATH!", True, sc)
            ss.set_alpha(pa)
            screen.blit(ss, ss.get_rect(center=(width // 2, height // 2 - 40)))
            remaining = max(0, 7 - (elapsed // 1000))
            cs = sub_font.render(f"Both reset to 0 in {remaining}...", True, WHITE)
            screen.blit(cs, cs.get_rect(center=(width // 2, height // 2 + 100)))

        elif game.state == STATE_WINNER:
            pf  = pygame.font.Font(None, 65)
            pa  = int(200 + 55 * math.sin(game.pulse_time * 3))

            ng  = pf.render("START = New Game", True, YELLOW)
            ng.set_alpha(pa)
            ng_rect = ng.get_rect(center=(width // 2, height - fh - 80))
            box = ng_rect.inflate(40, 30)
            pygame.draw.rect(screen, BLACK, box)
            pygame.draw.rect(screen, YELLOW, box, 3)
            screen.blit(ng, ng_rect)

            qt  = pf.render("SELECT = Back to Menu", True, WHITE)
            qt.set_alpha(pa)
            screen.blit(qt, qt.get_rect(center=(width // 2, height - fh - 30)))
            
        elif game.state == STATE_EDIT_SCORE:
            draw_edit_score_overlay(screen, game, width, height, hh, fh, btn_font, sub_font)


        # Confirmation dialogs always drawn on top
        if game.state == STATE_CONFIRM_RESTART:
            draw_confirm_dialog(screen, width, height, "Restart Game?",
                                btn_font, sub_font, game.pulse_time)
        elif game.state == STATE_CONFIRM_QUIT:
            draw_confirm_dialog(screen, width, height, "Quit to Menu?",
                                btn_font, sub_font, game.pulse_time)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()