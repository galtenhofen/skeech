        # Show welcome screen
        if game.show_welcome:
            # Draw game title
            title_mega_font = pygame.font.Font(None, 250)
            draw_glow_text(screen, "SKEECH", title_mega_font, WHITE, width // 2, height // 2 - 100, YELLOW, glow_amount=10)
            
            # Draw "Press Start" with pulsing effect
            press_start_font = pygame.font.Font(None, 80)
            pulse_alpha = int(200 + 55 * math.sin(game.pulse_time * 3))
            press_start_text = press_start_font.render("Press SPACE to Start", True, YELLOW)
            press_start_text.set_alpha(pulse_alpha)
            rect = press_start_text.get_rect(center=(width // 2, height // 2 + 150))
            screen.blit(press_start_text, rect)
            
            # Update display and continue to next frame
            pygame.display.flip()
            clock.tick(60)
            continue