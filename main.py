import random

import pygame
import settings as cfg
from screens.game_screen import run as game_screen, apply_bonus
from game.entities import Paddle, Brick, Ball, Bonus
from game.level import load_level

def _bounce_off_rect(ball: Ball, rect: pygame.Rect):
    """ Checks if the Ball collides with the given rect. """

    # Calculate ball's overlaps and find the smallest one
    overlap_left = ball.rect.right - rect.left
    overlap_right = rect.right - ball.rect.left
    overlap_top = ball.rect.bottom - rect.top
    overlap_bottom = rect.bottom - ball.rect.top

    min_overlap = min(
        overlap_bottom,
        overlap_left,
        overlap_right,
        overlap_top)
    
    # Calculate the Ball's final velocities
    if min_overlap == overlap_top and ball.vy > 0:
        print('top')
        ball.rect.bottom = rect.top
        ball.vy *= -1
    elif min_overlap == overlap_bottom and ball.vy < 0:
        print('bottom')

        ball.rect.top = rect.bottom
        ball.vy *= -1
    elif min_overlap == overlap_left and ball.vx > 0:
        print('left')

        ball.rect.right = rect.left
        ball.vx *= -1
    elif min_overlap == overlap_right and ball.vx < 0:
        print('right')

        ball.rect.left = rect.right
        ball.vx *= -1

def _handle_ball_vs_bricks(
    ball: Ball,
    bricks: list[Brick],
    bonuses: list[Bonus],
) -> int:

    scored = 0
    for brick in bricks[:]:  
        if not ball.rect.colliderect(brick.rect):
            continue
        _bounce_off_rect(ball, brick.rect)
        if brick.hp == -1: 
            continue
        brick.hit()

        if brick.hp <= 0:
            if random.random() < cfg.BONUS_PROBABILITY:
                bonus_type = random.choice(cfg.BONUS_TYPES)
                bonuses.append(Bonus(brick.rect.centerx, brick.rect.centery, bonus_type))
            bricks.remove(brick)
            scored += 10
    return scored

def _handle_ball_vs_paddle(ball: Ball, paddle: Paddle) -> None:
    """ Handles Ball bounce over the Paddle. """
    _bounce_off_rect(ball, paddle.rect)
    offset = (ball.rect.centerx - paddle.rect.centerx) / (paddle.rect.width / 2)
    max_vx = cfg.MAX_BALL_SPEED_X
    ball.vx = max(-max_vx, min(max_vx, offset * max_vx))

def main():
    pygame.init()
    screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
    pygame.display.set_caption("Arkanoid")
    clock = pygame.time.Clock()
    hud_font = pygame.font.SysFont(None, 24)

    running = True
    paddle = Paddle()

    bricks, rows, cols = load_level(1)
    balls = [Ball(cfg.WIDTH // 2, cfg.HEIGHT)]
    bonuses: list[Bonus] = []
    state = {"lives": 3, "score": 0}

    while running:
        # Main Loop
        screen.fill(cfg.BLACK)

        # Update Section
        keys = pygame.key.get_pressed()

        paddle.move(keys)

        for ball in balls:
            state["score"] += _handle_ball_vs_bricks(ball, bricks, bonuses)
            if ball.rect.colliderect(paddle.rect) and ball.vy > 0:
                _handle_ball_vs_paddle(ball, paddle)
            ball.update()

        # if every ball fell past the paddle, lose a life and respawn
        balls = [b for b in balls if b.rect.top < cfg.HEIGHT]
        if not balls:
            state["lives"] -= 1
            if state["lives"] <= 0:
                running = False
            else:
                balls = [Ball(cfg.WIDTH // 2, cfg.HEIGHT)]

        # bonuses falling / caught by paddle
        for bonus in bonuses[:]:
            bonus.update()
            if bonus.rect.colliderect(paddle.rect):
                apply_bonus(bonus.type, paddle, balls, state)
                bonuses.remove(bonus)
            elif bonus.rect.top > cfg.HEIGHT:
                bonuses.remove(bonus)

        for brick in bricks:
            brick.draw(screen)

        # Draw Section
        paddle.draw(screen)
        for ball in balls:
            ball.draw(screen)
        for bonus in bonuses:
            bonus.draw(screen)

        hud = hud_font.render(f"Score: {state['score']}   Lives: {state['lives']}", True, cfg.WHITE)
        screen.blit(hud, (cfg.FIELD_LEFT, 20))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:   # Press "close" button
                running = False

        pygame.display.flip()   # Screen Update
        clock.tick(cfg.FPS)         # FPS (Frames Per Second)

    pygame.quit()

if __name__ == "__main__":
    main()
