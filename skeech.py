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

# Screen setup - Full screen mode
screen = pygame.display.set_mode((1200,800))
pygame.display.set_caption("Scoreboard")
width, height = screen.get_size()

# Colors
BLUE = (37, 99, 235)
RED = (220, 38, 38)
GREY = (75, 85, 99)
DARK_GREY = (45, 45, 45)
YELLOW = (251, 191, 36)
GREEN = (52, 211, 153)
WHITE = (255, 255, 255)
BLACK = (26, 26, 26)
ORANGE = (255, 140, 0)

# Fonts
title_font = pygame.font.Font(None, 60)
score_font = pygame.font.Font(None, 500)
winner_font = pygame.font.Font(None, 150)
controls_font = pygame.font.Font(None, 40)
footer_font = pygame.font.Font(None, 35)

# Confetti particle class
class Confetti:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-15, -5)
        self.gravity = 0.5
        self.color = random.choice([YELLOW, GREEN, (255, 100, 100), (100, 100, 255), (255, 150, 0)])
        self.size = random.randint(5, 12)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-10, 10)
    
    def update(self):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.rotation += self.rotation_speed
    
    def draw(self, surface):
        points = []
        for i in range(4):
            angle = math.radians(self.rotation + i * 90)
            px = self.x + math.cos(angle) * self.size
            py = self.y + math.sin(angle) * self.size
            points.append((px, py))
        pygame.draw.polygon(surface, self.color, points)

# Game states
STATE_WELCOME = "welcome"
STATE_PLAYING = "playing"
STATE_OVER_21 = "over_21"          # Pulsing "You Went Over" message
STATE_RETRIBUTION = "retribution"  # "Retribution?" dialog
STATE_RETRIBUTION_WAIT = "retribution_wait"  # Other player tries to reach 21
STATE_SUDDEN_DEATH = "sudden_death"  # Both at 21 - flash "Sudden Death!"
STATE_WINNER = "winner"
STATE_DECLARE_WINNER = "declare_winner"  # Confirm declare-winner dialog
STATE_CONFIRM_QUIT = "confirm_quit"      # Confirm before returning to welcome screen

class GameState:
    def __init__(self):
        self.player1_score = 0
        self.player2_score = 0
        self.game_active = False
        self.winner = None
        self.score_history = []
        self.pulse_time = 0
        self.confetti = []
        self.winner_announced_time = None
        self.show_welcome = True
        self.state = STATE_WELCOME

        # Over-21 tracking
        self.over21_player = None        # which player went over
        self.over21_start_time = None    # when the over-21 message started

        # Retribution tracking
        self.retribution_player = None   # player who hit 21 first
        self.retribution_start_time = None

        # Sudden death
        self.sudden_death_start_time = None

        # Declare winner
        self.declare_winner_player = None
        self.pre_declare_state = None

        # Quit confirmation
        self.pre_quit_state = None

    def go_to_welcome(self):
        self.__init__()

    def start_game(self):
        self.player1_score = 0
        self.player2_score = 0
        self.game_active = True
        self.winner = None
        self.score_history = []
        self.confetti = []
        self.winner_announced_time = None
        self.show_welcome = False
        self.state = STATE_PLAYING
        self.over21_player = None
        self.over21_start_time = None
        self.retribution_player = None
        self.retribution_start_time = None
        self.sudden_death_start_time = None
        self.declare_winner_player = None
        self.pre_declare_state = None

    def add_score(self, player, points):
        if self.state not in (STATE_PLAYING, STATE_RETRIBUTION_WAIT):
            return

        if player == 1:
            self.score_history.append({
                'player': 1,
                'prev_score': self.player1_score,
                'points': points
            })
            self.player1_score += points
        else:
            self.score_history.append({
                'player': 2,
                'prev_score': self.player2_score,
                'points': points
            })
            self.player2_score += points

        self.check_score(player)

    def check_score(self, player):
        score = self.player1_score if player == 1 else self.player2_score

        if score > 21:
            # Over 21 - set score to 15 and show message
            if player == 1:
                self.player1_score = 15
            else:
                self.player2_score = 15
            self.over21_player = player
            self.over21_start_time = pygame.time.get_ticks()
            self.state = STATE_OVER_21

        elif score == 21:
            if self.state == STATE_RETRIBUTION_WAIT:
                # Other player also hit 21 → Sudden Death
                self.sudden_death_start_time = pygame.time.get_ticks()
                self.state = STATE_SUDDEN_DEATH
            else:
                # First player to hit 21 → ask for Retribution
                self.retribution_player = player
                self.retribution_start_time = pygame.time.get_ticks()
                self.state = STATE_RETRIBUTION

    def undo(self):
        if len(self.score_history) == 0:
            return
        last_move = self.score_history.pop()
        if last_move['player'] == 1:
            self.player1_score = last_move['prev_score']
        else:
            self.player2_score = last_move['prev_score']
        self.winner = None
        self.state = STATE_PLAYING
        self.game_active = True

    def spawn_confetti(self):
        for _ in range(100):
            x = random.randint(0, width)
            y = random.randint(-100, height // 3)
            self.confetti.append(Confetti(x, y))

    def update_confetti(self):
        for c in self.confetti[:]:
            c.update()
            if c.y > height + 50:
                self.confetti.remove(c)


def get_winner_text_scale(time_since_win):
    if time_since_win < 500:
        return 1.0 + 0.5 * (time_since_win / 500)
    else:
        bounce = abs(math.sin((time_since_win - 500) / 200))
        return 1.5 + bounce * 0.3

def get_winner_text_color(pulse_time):
    r = int(127 + 127 * math.sin(pulse_time * 3))
    g = int(127 + 127 * math.sin(pulse_time * 3 + 2))
    b = int(127 + 127 * math.sin(pulse_time * 3 + 4))
    return (r, g, b)

def draw_text_centered(surface, text, font, color, x, y):
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, rect)

def draw_text(surface, text, font, color, x, y):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))

def draw_glow_text(surface, text, font, color, x, y, glow_color, glow_amount=8):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    for offset in range(glow_amount, 0, -1):
        alpha = 255 - (offset * 255 // glow_amount)
        glow_size = offset * 2
        glow_surface = pygame.Surface((text_surface.get_width() + glow_size * 2,
                                       text_surface.get_height() + glow_size * 2),
                                      pygame.SRCALPHA)
        glow_text = font.render(text, True, glow_color)
        glow_text.set_alpha(alpha)
        glow_rect = glow_text.get_rect(center=(glow_surface.get_width() // 2,
                                               glow_surface.get_height() // 2))
        glow_surface.blit(glow_text, glow_rect)
        glow_rect = glow_surface.get_rect(center=(x, y))
        surface.blit(glow_surface, glow_rect)
    surface.blit(text_surface, text_rect)

def get_pulse_brightness(pulse_time):
    return 1.2 + 0.4 * abs(math.sin(pulse_time * 2))

def draw_scoreboard(screen, game, width, height, header_height, footer_height, scoreboard_height, half_width):
    """Draw the main scoreboard background and scores."""
    # Determine colors for each side
    if game.winner == 1:
        p1_color = tuple(min(255, int(c * get_pulse_brightness(game.pulse_time))) for c in BLUE)
        p2_color = GREY
    elif game.winner == 2:
        p1_color = GREY
        p2_color = tuple(min(255, int(c * get_pulse_brightness(game.pulse_time))) for c in RED)
    else:
        p1_color = BLUE
        p2_color = RED

    pygame.draw.rect(screen, p1_color, (0, header_height, half_width, scoreboard_height))
    pygame.draw.rect(screen, p2_color, (half_width, header_height, half_width, scoreboard_height))

    if game.winner == 2:
        overlay = pygame.Surface((half_width, scoreboard_height))
        overlay.set_alpha(128)
        overlay.fill(GREY)
        screen.blit(overlay, (0, header_height))
    elif game.winner == 1:
        overlay = pygame.Surface((half_width, scoreboard_height))
        overlay.set_alpha(128)
        overlay.fill(GREY)
        screen.blit(overlay, (half_width, header_height))

    pygame.draw.line(screen, BLACK, (half_width, header_height), (half_width, height - footer_height), 4)

    # Winner text
    if game.winner == 1:
        time_since_win = pygame.time.get_ticks() - game.winner_announced_time
        scale = get_winner_text_scale(time_since_win)
        winner_color = get_winner_text_color(game.pulse_time)
        scaled_font = pygame.font.Font(None, int(150 * scale))
        draw_glow_text(screen, "WINNER", scaled_font, winner_color,
                       half_width // 2, header_height + 220, YELLOW, glow_amount=8)

    draw_text_centered(screen, str(game.player1_score), score_font, WHITE,
                       half_width // 2, header_height + scoreboard_height // 2)

    if game.winner == 2:
        time_since_win = pygame.time.get_ticks() - game.winner_announced_time
        scale = get_winner_text_scale(time_since_win)
        winner_color = get_winner_text_color(game.pulse_time)
        scaled_font = pygame.font.Font(None, int(150 * scale))
        draw_glow_text(screen, "WINNER", scaled_font, winner_color,
                       half_width + half_width // 2, header_height + 220, YELLOW, glow_amount=8)

    draw_text_centered(screen, str(game.player2_score), score_font, WHITE,
                       half_width + half_width // 2, header_height + scoreboard_height // 2)

    # Header / Footer
    pygame.draw.rect(screen, DARK_GREY, (0, 0, width, header_height))
    pygame.draw.rect(screen, DARK_GREY, (0, height - footer_height, width, footer_height))


def draw_overlay_box(screen, width, height, bg_color=(20, 20, 20), alpha=220):
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((*bg_color, alpha))
    screen.blit(overlay, (0, 0))


def main():
    game = GameState()
    clock = pygame.time.Clock()
    running = True

#    if pygame.joystick.get_count() > 0:
#        joystick = pygame.joystick.Joystick(0)
#        joystick.init()
#    if pygame.joystick.get_count() > 1:
#        joystick2 = pygame.joystick.Joystick(1)
#        joystick2.init()
#    if pygame.joystick.get_count() > 2:
#        joystick3= pygame.joystick.Joystick(2)
#        joystick3.init()

    header_height = 20
    footer_height = 20
    scoreboard_height = height - header_height - footer_height
    half_width = width // 2

    msg_font = pygame.font.Font(None, 120)
    sub_font = pygame.font.Font(None, 70)
    btn_font = pygame.font.Font(None, 80)

    OVER21_DISPLAY_MS = 2000  # how long to show "You Went Over" before resuming

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.JOYBUTTONDOWN:
                print(f"Joystick {event.joy} Button {event.button} pressed")

                # Track quit-hold start
                if event.joy == 2 and event.button == 6:
                    game.pre_quit_state = game.state
                    game.state = STATE_CONFIRM_QUIT

                # ---- Confirm Quit dialog ----
                elif game.state == STATE_CONFIRM_QUIT:
                    if event.joy == 2 and event.button == 5:   # White = Yes, go to welcome
                        game.go_to_welcome()
                    elif event.joy == 2 and event.button == 1: # Black = No, cancel
                        game.state = game.pre_quit_state

                # ---- Declare Winner confirm dialog ----
                elif game.state == STATE_DECLARE_WINNER:
                    if event.joy == 2 and event.button == 1:   # Black = confirm
                        game.winner = game.declare_winner_player
                        game.game_active = False
                        game.winner_announced_time = now
                        game.declare_winner_player = None
                        game.state = STATE_WINNER
                    elif event.joy == 2 and event.button == 5: # White = cancel
                        game.state = game.pre_declare_state
                        game.declare_winner_player = None

                elif event.joy == 2 and event.button == 0:
                    game.start_game()

                # ---- Retribution dialog: White=game over, Black=retribution ----
                elif game.state == STATE_RETRIBUTION:
                    if event.joy == 2 and event.button == 5:
                        # White → current player wins (game over)
                        game.winner = game.retribution_player
                        game.game_active = False
                        game.winner_announced_time = now
                        game.state = STATE_WINNER
                    elif event.joy == 2 and event.button == 1:
                        # Black → other player gets a chance
                        game.state = STATE_RETRIBUTION_WAIT
                        game.game_active = True

                # ---- Retribution Wait: Black declare = declare retribution player winner ----
                elif game.state == STATE_RETRIBUTION_WAIT:
                    if event.joy == 2 and event.button == 1:   # Black = declare winner
                        game.declare_winner_player = game.retribution_player
                        game.pre_declare_state = STATE_RETRIBUTION_WAIT
                        game.state = STATE_DECLARE_WINNER
                    # Normal scoring still works during retribution wait
                    elif event.joy == 0 and event.button == 0:
                        game.add_score(1, 1)
                    elif event.joy == 0 and event.button == 1:
                        game.add_score(1, 3)
                    elif event.joy == 0 and event.button == 2:
                        game.add_score(1, 5)
                    elif event.joy == 0 and event.button == 10:
                        game.add_score(1, 3)
                    elif event.joy == 0 and event.button == 11:
                        game.add_score(1, 1)
                    elif event.joy == 1 and event.button == 0:
                        game.add_score(2, 1)
                    elif event.joy == 1 and event.button == 1:
                        game.add_score(2, 3)
                    elif event.joy == 1 and event.button == 2:
                        game.add_score(2, 5)
                    elif event.joy == 1 and event.button == 10:
                        game.add_score(2, 3)
                    elif event.joy == 1 and event.button == 11:
                        game.add_score(2, 1)

                # ---- Sudden Death: Black declare = declare leading player winner ----
                elif game.state == STATE_SUDDEN_DEATH:
                    if event.joy == 2 and event.button == 1:
                        if game.player1_score > game.player2_score:
                            leading = 1
                        elif game.player2_score > game.player1_score:
                            leading = 2
                        else:
                            leading = 1  # tie: default to player 1 / Blue
                        game.declare_winner_player = leading
                        game.pre_declare_state = STATE_SUDDEN_DEATH
                        game.state = STATE_DECLARE_WINNER

                # ---- Normal gameplay ----
                elif game.state == STATE_PLAYING:
                    if event.joy == 0 and event.button == 0:
                        game.add_score(1, 1)
                    elif event.joy == 0 and event.button == 1:
                        game.add_score(1, 3)
                    elif event.joy == 0 and event.button == 2:
                        game.add_score(1, 5)
                    elif event.joy == 0 and event.button == 10:
                        game.add_score(1, 3)
                    elif event.joy == 0 and event.button == 11:
                        game.add_score(1, 1)
                    elif event.joy == 1 and event.button == 0:
                        game.add_score(2, 1)
                    elif event.joy == 1 and event.button == 1:
                        game.add_score(2, 3)
                    elif event.joy == 1 and event.button == 2:
                        game.add_score(2, 5)
                    elif event.joy == 1 and event.button == 10:
                        game.add_score(2, 3)
                    elif event.joy == 1 and event.button == 11:
                        game.add_score(2, 1)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game.pre_quit_state = game.state
                    game.state = STATE_CONFIRM_QUIT

                # ---- Confirm Quit dialog (keyboard) ----
                elif game.state == STATE_CONFIRM_QUIT:
                    if event.key == pygame.K_y:
                        game.go_to_welcome()
                    elif event.key == pygame.K_n:
                        game.state = game.pre_quit_state

                elif event.key == pygame.K_SPACE:
                    game.start_game()
                elif event.key == pygame.K_BACKSPACE:
                    game.undo()

                # ---- Declare Winner confirm (keyboard) ----
                elif game.state == STATE_DECLARE_WINNER:
                    if event.key == pygame.K_RETURN:
                        game.winner = game.declare_winner_player
                        game.game_active = False
                        game.winner_announced_time = now
                        game.declare_winner_player = None
                        game.state = STATE_WINNER
                    elif event.key == pygame.K_x:
                        game.state = game.pre_declare_state
                        game.declare_winner_player = None

                # ---- Retribution dialog keyboard: N = No, Y = Yes ----
                elif game.state == STATE_RETRIBUTION:
                    if event.key == pygame.K_n:
                        game.winner = game.retribution_player
                        game.game_active = False
                        game.winner_announced_time = now
                        game.state = STATE_WINNER
                    elif event.key == pygame.K_y:
                        game.state = STATE_RETRIBUTION_WAIT
                        game.game_active = True

                # ---- Retribution Wait: D = declare winner ----
                elif game.state == STATE_RETRIBUTION_WAIT:
                    if event.key == pygame.K_d:
                        game.declare_winner_player = game.retribution_player
                        game.pre_declare_state = STATE_RETRIBUTION_WAIT
                        game.state = STATE_DECLARE_WINNER
                    elif event.key == pygame.K_q:
                        game.add_score(1, 1)
                    elif event.key == pygame.K_w:
                        game.add_score(1, 3)
                    elif event.key == pygame.K_e:
                        game.add_score(1, 5)
                    elif event.key == pygame.K_i:
                        game.add_score(2, 1)
                    elif event.key == pygame.K_o:
                        game.add_score(2, 3)
                    elif event.key == pygame.K_p:
                        game.add_score(2, 5)

                # ---- Sudden Death: D = declare winner ----
                elif game.state == STATE_SUDDEN_DEATH:
                    if event.key == pygame.K_d:
                        leading = 1 if game.player1_score >= game.player2_score else 2
                        game.declare_winner_player = leading
                        game.pre_declare_state = STATE_SUDDEN_DEATH
                        game.state = STATE_DECLARE_WINNER

                # ---- Normal gameplay ----
                elif game.state == STATE_PLAYING:
                    if event.key == pygame.K_q:
                        game.add_score(1, 1)
                    elif event.key == pygame.K_w:
                        game.add_score(1, 3)
                    elif event.key == pygame.K_e:
                        game.add_score(1, 5)
                    elif event.key == pygame.K_i:
                        game.add_score(2, 1)
                    elif event.key == pygame.K_o:
                        game.add_score(2, 3)
                    elif event.key == pygame.K_p:
                        game.add_score(2, 5)

        # ---- Auto-transitions ----

        # Over-21: after display time, resume play
        if game.state == STATE_OVER_21:
            if now - game.over21_start_time >= OVER21_DISPLAY_MS:
                game.state = STATE_PLAYING
                game.over21_player = None
                game.over21_start_time = None

        # Sudden Death: after 7 seconds, reset both scores to 0
        if game.state == STATE_SUDDEN_DEATH:
            if now - game.sudden_death_start_time >= 5000:
                game.player1_score = 0
                game.player2_score = 0
                game.retribution_player = None
                game.state = STATE_PLAYING

        # Update pulse
        game.pulse_time += clock.get_time() / 1000.0

        # ---- RENDER ----
        screen.fill(BLACK)

        # Welcome screen
        if game.state == STATE_WELCOME:
            title_mega_font = pygame.font.SysFont('freeserif', 400)
            draw_glow_text(screen, "SKEECH", title_mega_font, WHITE, width // 2, height // 2 - 100, YELLOW, glow_amount=10)
            press_start_font = pygame.font.Font(None, 80)
            pulse_alpha = int(200 + 55 * math.sin(game.pulse_time * 3))
            press_start_text = press_start_font.render("Press Start To Play", True, YELLOW)
            press_start_text.set_alpha(pulse_alpha)
            rect = press_start_text.get_rect(center=(width // 2, height // 2 + 150))
            screen.blit(press_start_text, rect)
            pygame.display.flip()
            clock.tick(60)
            continue

        # Draw the base scoreboard
        draw_scoreboard(screen, game, width, height, header_height, footer_height, scoreboard_height, half_width)

        # ---- STATE-SPECIFIC OVERLAYS ----

        if game.state == STATE_OVER_21:
            # Semi-transparent dark overlay
            draw_overlay_box(screen, width, height)
            elapsed = now - game.over21_start_time
            pulse_alpha = int(180 + 75 * math.sin(elapsed / 120.0))
            over_font = pygame.font.Font(None, 140)
            over_surf = over_font.render("You Went Over!", True, ORANGE)
            over_surf.set_alpha(pulse_alpha)
            over_rect = over_surf.get_rect(center=(width // 2, height // 2 - 60))
            screen.blit(over_surf, over_rect)

            #sub_surf = sub_font.render(f"Player {game.over21_player} score reset to 15", True, WHITE)
            #sub_surf.set_alpha(pulse_alpha)
            #sub_rect = sub_surf.get_rect(center=(width // 2, height // 2 + 60))
            #screen.blit(sub_surf, sub_rect)

        elif game.state == STATE_RETRIBUTION:
            draw_overlay_box(screen, width, height)

            # Pulsing "Retribution?" title
            ret_font = pygame.font.Font(None, 160)
            pulse_alpha = int(200 + 55 * math.sin(game.pulse_time * 4))
            ret_surf = ret_font.render("Retribution?", True, YELLOW)
            ret_surf.set_alpha(pulse_alpha)
            screen.blit(ret_surf, ret_surf.get_rect(center=(width // 2, height // 2 - 130)))

            # Stacked message panel
            msg_font2 = pygame.font.Font(None, 62)
            white_surf = msg_font2.render("White Button = Game Over",   True, WHITE)
            black_surf = msg_font2.render("Black Button = Retribution", True, (20, 20, 20))

            pad_x, pad_y, row_gap = 40, 24, 14
            panel_w = max(white_surf.get_width(), black_surf.get_width()) + pad_x * 2
            panel_h = white_surf.get_height() + black_surf.get_height() + pad_y * 2 + row_gap
            panel_x = width  // 2 - panel_w // 2
            panel_y = height // 2 - 10

            panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel_surf.fill((80, 85, 95, 235))
            screen.blit(panel_surf, (panel_x, panel_y))
            pygame.draw.rect(screen, WHITE, pygame.Rect(panel_x, panel_y, panel_w, panel_h), width=3, border_radius=8)

            row1_y = panel_y + pad_y
            screen.blit(white_surf, white_surf.get_rect(center=(width // 2, row1_y + white_surf.get_height() // 2)))

            div_y = row1_y + white_surf.get_height() + row_gap // 2
            pygame.draw.line(screen, (140, 145, 155), (panel_x + 20, div_y), (panel_x + panel_w - 20, div_y), 1)

            row2_y = div_y + row_gap // 2
            strip_h = black_surf.get_height() + pad_y
            strip = pygame.Surface((panel_w - 6, strip_h), pygame.SRCALPHA)
            strip.fill((215, 215, 215, 250))
            strip_rect = pygame.Rect(panel_x + 3, row2_y, panel_w - 6, strip_h)
            screen.blit(strip, strip_rect)
            pygame.draw.rect(screen, (120, 120, 120), strip_rect, width=2, border_radius=5)
            screen.blit(black_surf, black_surf.get_rect(center=(width // 2, row2_y + strip_h // 2)))

        elif game.state == STATE_RETRIBUTION_WAIT:
            # Banner telling the other player to try for 21
            # other_player = 2 if game.retribution_player == 1 else 1
            # banner_font = pygame.font.Font(None, 70)
            # pulse_alpha = int(180 + 75 * math.sin(game.pulse_time * 3))
            # banner_surf = banner_font.render(f"Player {other_player}: Score 21 for Retribution!", True, YELLOW)
            # banner_surf.set_alpha(pulse_alpha)
            # banner_rect = banner_surf.get_rect(center=(width // 2, height - footer_height - 80))
            # pad = 18
            # bg_rect = banner_rect.inflate(pad * 2, pad * 2)
            # bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            # bg_surf.fill((0, 0, 0, 170))
            # screen.blit(bg_surf, bg_rect.topleft)
            # screen.blit(banner_surf, banner_rect)

            # "Press Black to Declare Winner" banner below
            declare_font = pygame.font.Font(None, 50)
            pulse_alpha2 = int(160 + 75 * math.sin(game.pulse_time * 2.5 + 1))
            declare_surf = declare_font.render("Press Black to Declare Winner", True, WHITE)
            declare_surf.set_alpha(pulse_alpha2)
            declare_rect = declare_surf.get_rect(center=(width // 2, height - footer_height - 30))
            bg_declare = pygame.Surface((declare_rect.width + 30, declare_rect.height + 10), pygame.SRCALPHA)
            bg_declare.fill((0, 0, 0, 150))
            screen.blit(bg_declare, bg_declare.get_rect(center=declare_rect.center))
            screen.blit(declare_surf, declare_rect)

        elif game.state == STATE_SUDDEN_DEATH:
            elapsed = now - game.sudden_death_start_time
            draw_overlay_box(screen, width, height, bg_color=(0, 0, 0), alpha=200)
            sd_font = pygame.font.Font(None, 220)
            pulse_alpha = int(160 + 95 * math.sin(elapsed / 150.0))
            sd_color = get_winner_text_color(game.pulse_time)
            sd_surf = sd_font.render("SUDDEN DEATH!", True, sd_color)
            sd_surf.set_alpha(pulse_alpha)
            sd_rect = sd_surf.get_rect(center=(width // 2, height // 2 - 60))
            screen.blit(sd_surf, sd_rect)

            remaining = max(0, 7 - (elapsed // 1000))
            #countdown_surf = sub_font.render(f"Both reset to 0 in {remaining}...", True, WHITE)
            #countdown_rect = countdown_surf.get_rect(center=(width // 2, height // 2 + 60))
            #screen.blit(countdown_surf, countdown_rect)

            # "Press Black to Declare Winner" banner
            declare_font = pygame.font.Font(None, 52)
            pulse_alpha2 = int(180 + 75 * math.sin(game.pulse_time * 2.5))
            declare_surf = declare_font.render("Press Black to Declare Winner", True, WHITE)
            declare_surf.set_alpha(pulse_alpha2)
            declare_rect = declare_surf.get_rect(center=(width // 2, height - footer_height - 40))
            bg_declare = pygame.Surface((declare_rect.width + 30, declare_rect.height + 14), pygame.SRCALPHA)
            bg_declare.fill((0, 0, 0, 160))
            screen.blit(bg_declare, bg_declare.get_rect(center=declare_rect.center))
            screen.blit(declare_surf, declare_rect)

        elif game.state == STATE_DECLARE_WINNER:
            draw_overlay_box(screen, width, height)
            player_name = "Blue" if game.declare_winner_player == 1 else "Red"
            name_color  = BLUE   if game.declare_winner_player == 1 else RED

            dw_font = pygame.font.Font(None, 110)
            pulse_alpha = int(200 + 55 * math.sin(game.pulse_time * 4))
            dw_surf = dw_font.render(f"Declare {player_name} Winner?", True, name_color)
            dw_surf.set_alpha(pulse_alpha)
            screen.blit(dw_surf, dw_surf.get_rect(center=(width // 2, height // 2 - 80)))

            msg_font3   = pygame.font.Font(None, 60)
            conf_surf   = msg_font3.render("Black Button = Confirm", True, (20, 20, 20))
            cancel_surf = msg_font3.render("White Button = Cancel",  True, WHITE)

            pad_x, pad_y, row_gap = 40, 24, 14
            panel_w = max(conf_surf.get_width(), cancel_surf.get_width()) + pad_x * 2
            panel_h = conf_surf.get_height() + cancel_surf.get_height() + pad_y * 2 + row_gap
            panel_x = width  // 2 - panel_w // 2
            panel_y = height // 2 + 20

            panel_surf2 = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel_surf2.fill((80, 85, 95, 235))
            screen.blit(panel_surf2, (panel_x, panel_y))
            pygame.draw.rect(screen, WHITE, pygame.Rect(panel_x, panel_y, panel_w, panel_h), width=3, border_radius=8)

            # Row 1: Black = confirm on light strip
            row1_y = panel_y + pad_y
            strip1_h = conf_surf.get_height() + pad_y
            strip1 = pygame.Surface((panel_w - 6, strip1_h), pygame.SRCALPHA)
            strip1.fill((215, 215, 215, 250))
            strip1_rect = pygame.Rect(panel_x + 3, row1_y, panel_w - 6, strip1_h)
            screen.blit(strip1, strip1_rect)
            pygame.draw.rect(screen, (120, 120, 120), strip1_rect, width=2, border_radius=5)
            screen.blit(conf_surf, conf_surf.get_rect(center=(width // 2, row1_y + strip1_h // 2)))

            div_y = row1_y + strip1_h + row_gap // 2
            pygame.draw.line(screen, (140, 145, 155), (panel_x + 20, div_y), (panel_x + panel_w - 20, div_y), 1)

            # Row 2: White = cancel on dark background
            row2_y = div_y + row_gap // 2
            screen.blit(cancel_surf, cancel_surf.get_rect(center=(width // 2, row2_y + cancel_surf.get_height() // 2 + 8)))

        elif game.state == STATE_WINNER:
            press_start_font = pygame.font.Font(None, 80)
            pulse_alpha = int(200 + 55 * math.sin(game.pulse_time * 3))
            press_start_text = press_start_font.render("Press Start To Play Again", True, YELLOW)
            press_start_text.set_alpha(pulse_alpha)
            rect = press_start_text.get_rect(center=(width // 2, height // 2 + 300))
            padding = 20
            box_rect = pygame.Rect(rect.x - padding, rect.y - padding, rect.width + padding * 2, rect.height + padding * 2)
            pygame.draw.rect(screen, BLACK, box_rect)
            pygame.draw.rect(screen, YELLOW, box_rect, 3)
            screen.blit(press_start_text, rect)

        # Confirm Quit overlay — drawn on top of any state
        if game.state == STATE_CONFIRM_QUIT:
            draw_overlay_box(screen, width, height)

            cf = pygame.font.Font(None, 130)
            pulse_alpha = int(200 + 55 * math.sin(game.pulse_time * 4))
            cs = cf.render("Quit to Menu?", True, YELLOW)
            cs.set_alpha(pulse_alpha)
            screen.blit(cs, cs.get_rect(center=(width // 2, height // 2 - 100)))

            msg_font2 = pygame.font.Font(None, 62)
            yes_surf = msg_font2.render("White Button = Yes", True, WHITE)
            no_surf  = msg_font2.render("Black Button = No",  True, (20, 20, 20))

            pad_x, pad_y, row_gap = 40, 24, 14
            panel_w = max(yes_surf.get_width(), no_surf.get_width()) + pad_x * 2
            panel_h = yes_surf.get_height() + no_surf.get_height() + pad_y * 2 + row_gap
            panel_x = width  // 2 - panel_w // 2
            panel_y = height // 2 + 10

            panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel_surf.fill((80, 85, 95, 235))
            screen.blit(panel_surf, (panel_x, panel_y))
            pygame.draw.rect(screen, WHITE, pygame.Rect(panel_x, panel_y, panel_w, panel_h), width=3, border_radius=8)

            row1_y = panel_y + pad_y
            screen.blit(yes_surf, yes_surf.get_rect(center=(width // 2, row1_y + yes_surf.get_height() // 2)))

            div_y = row1_y + yes_surf.get_height() + row_gap // 2
            pygame.draw.line(screen, (140, 145, 155), (panel_x + 20, div_y), (panel_x + panel_w - 20, div_y), 1)

            row2_y = div_y + row_gap // 2
            strip_h = no_surf.get_height() + pad_y
            strip = pygame.Surface((panel_w - 6, strip_h), pygame.SRCALPHA)
            strip.fill((215, 215, 215, 250))
            strip_rect = pygame.Rect(panel_x + 3, row2_y, panel_w - 6, strip_h)
            screen.blit(strip, strip_rect)
            pygame.draw.rect(screen, (120, 120, 120), strip_rect, width=2, border_radius=5)
            screen.blit(no_surf, no_surf.get_rect(center=(width // 2, row2_y + strip_h // 2)))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
