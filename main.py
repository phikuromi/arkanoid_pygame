import math
import random

import pygame
import settings as cfg
from screens.game_screen import apply_bonus
from game.entities import Paddle, Brick, Ball, Bonus
from game.level import load_level

MENU = "menu"
PLAYING = "playing"
GAME_OVER = "game_over"
WIN = "win"

TOTAL_LEVELS = 3


def _bounce_off_rect(ball: Ball, rect: pygame.Rect) -> None:
    """ Checks if the Ball collides with the given rect and reflects it off the nearest edge. """

    overlap_left = ball.rect.right - rect.left
    overlap_right = rect.right - ball.rect.left
    overlap_top = ball.rect.bottom - rect.top
    overlap_bottom = rect.bottom - ball.rect.top

    min_overlap = min(overlap_bottom, overlap_left, overlap_right, overlap_top)

    if min_overlap == overlap_top and ball.vy > 0:
        ball.rect.bottom = rect.top
        ball.vy *= -1
    elif min_overlap == overlap_bottom and ball.vy < 0:
        ball.rect.top = rect.bottom
        ball.vy *= -1
    elif min_overlap == overlap_left and ball.vx > 0:
        ball.rect.right = rect.left
        ball.vx *= -1
    elif min_overlap == overlap_right and ball.vx < 0:
        ball.rect.left = rect.right
        ball.vx *= -1


def _handle_ball_vs_bricks(ball: Ball, bricks: list[Brick], bonuses: list[Bonus]) -> int:
    scored = 0
    for brick in bricks[:]:
        if not ball.rect.colliderect(brick.rect):
            continue
        _bounce_off_rect(ball, brick.rect)
        if brick.hp <= 0:  # indestructible brick or level boundary
            break
        brick.hit()
        if brick.hp <= 0:
            if random.random() < cfg.BONUS_PROBABILITY:
                bonus_type = random.choice(cfg.BONUS_TYPES)
                bonuses.append(Bonus(brick.rect.centerx, brick.rect.centery, bonus_type))
            bricks.remove(brick)
            scored += 10
        break
    return scored


def _handle_ball_vs_paddle(ball: Ball, paddle: Paddle) -> None:
    """ Handles the ball bouncing off the paddle, angled by where it lands. """
    _bounce_off_rect(ball, paddle.rect)
    offset = (ball.rect.centerx - paddle.rect.centerx) / (paddle.rect.width / 2)
    max_vx = cfg.MAX_BALL_SPEED_X
    ball.vx = max(-max_vx, min(max_vx, offset * max_vx))

    # changing vx alone could push the total speed above BALL_MAX_SPEED - clamp it back
    speed = math.hypot(ball.vx, ball.vy)
    if speed > cfg.BALL_MAX_SPEED:
        scale = cfg.BALL_MAX_SPEED / speed
        ball.vx *= scale
        ball.vy *= scale


def _new_level_state(level: int) -> dict:
    bricks, _, _ = load_level(level)
    return {
        "paddle": Paddle(),
        "bricks": bricks,
        "balls": [Ball(cfg.WIDTH // 2, cfg.HEIGHT)],
        "bonuses": [],
    }


def _draw_menu(screen, font, big_font) -> None:
    title = big_font.render("ARKANOID", True, cfg.CYAN)
    screen.blit(title, title.get_rect(center=(cfg.WIDTH // 2, cfg.HEIGHT // 2 - 40)))

    prompt = font.render("Press SPACE to start", True, cfg.WHITE)
    screen.blit(prompt, prompt.get_rect(center=(cfg.WIDTH // 2, cfg.HEIGHT // 2 + 20)))


def _draw_end_screen(screen, font, big_font, title, color, score) -> None:
    title_surf = big_font.render(title, True, color)
    screen.blit(title_surf, title_surf.get_rect(center=(cfg.WIDTH // 2, cfg.HEIGHT // 2 - 40)))

    score_surf = font.render(f"Final Score: {score}", True, cfg.WHITE)
    screen.blit(score_surf, score_surf.get_rect(center=(cfg.WIDTH // 2, cfg.HEIGHT // 2 + 10)))

    prompt = font.render("Press SPACE to play again", True, cfg.WHITE)
    screen.blit(prompt, prompt.get_rect(center=(cfg.WIDTH // 2, cfg.HEIGHT // 2 + 45)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
    pygame.display.set_caption("Arkanoid")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 26)
    big_font = pygame.font.SysFont(None, 64)
    hud_font = pygame.font.SysFont(None, 24)

    game_state = MENU
    level = 1
    level_state = _new_level_state(level)
    score = 0
    lives = 3
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if game_state == MENU:
                    game_state = PLAYING
                elif game_state in (GAME_OVER, WIN):
                    level = 1
                    score = 0
                    lives = 3
                    level_state = _new_level_state(level)
                    game_state = PLAYING

        keys = pygame.key.get_pressed()
        screen.fill(cfg.BLACK)

        if game_state == MENU:
            _draw_menu(screen, font, big_font)

        elif game_state == PLAYING:
            paddle = level_state["paddle"]
            bricks = level_state["bricks"]
            balls = level_state["balls"]
            bonuses = level_state["bonuses"]

            paddle.move(keys)

            for ball in balls:
                score += _handle_ball_vs_bricks(ball, bricks, bonuses)
                if ball.rect.colliderect(paddle.rect) and ball.vy > 0:
                    _handle_ball_vs_paddle(ball, paddle)
                ball.update()

            balls = level_state["balls"] = [b for b in balls if b.rect.top < cfg.HEIGHT]
            if not balls:
                lives -= 1
                if lives <= 0:
                    game_state = GAME_OVER
                else:
                    level_state["balls"] = [Ball(cfg.WIDTH // 2, cfg.HEIGHT)]
                    level_state["paddle"] = Paddle()

            for bonus in bonuses[:]:
                bonus.update()
                if bonus.rect.colliderect(paddle.rect):
                    apply_bonus(bonus.type, paddle, balls, {"lives": lives})
                    bonuses.remove(bonus)
                elif bonus.rect.top > cfg.HEIGHT:
                    bonuses.remove(bonus)

            # level cleared - move to the next one, or win the game
            if game_state == PLAYING and not any(b.hp > 0 for b in bricks):
                if level < TOTAL_LEVELS:
                    level += 1
                    level_state = _new_level_state(level)
                else:
                    game_state = WIN

            if game_state == PLAYING:
                for brick in bricks:
                    brick.draw(screen)
                paddle.draw(screen)
                for ball in balls:
                    ball.draw(screen)
                for bonus in bonuses:
                    bonus.draw(screen)

                hud = hud_font.render(f"Score: {score}   Level: {level}   Lives: {lives}", True, cfg.WHITE)
                screen.blit(hud, (cfg.FIELD_LEFT, 20))

        else:
            if game_state == WIN:
                _draw_end_screen(screen, font, big_font, "YOU WIN!", cfg.GREEN, score)
            else:
                _draw_end_screen(screen, font, big_font, "GAME OVER", cfg.RED, score)

        pygame.display.flip()
        clock.tick(cfg.FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
