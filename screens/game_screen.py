import math

import pygame
import settings as cfg
from game.entities import Paddle, Ball

def run(screen: pygame.Surface, clock: pygame.time.Clock, level: int) -> None:
    paddle = Paddle()

    keys = pygame.key.get_pressed()
    paddle.move(keys)

    paddle.draw(screen)


def _resize_paddle(paddle: Paddle, delta_width: int) -> None:
    center_x = paddle.rect.centerx
    new_width = paddle.rect.width + delta_width
    new_width = max(cfg.PADDLE_MIN_WIDTH, min(cfg.PADDLE_MAX_WIDTH, new_width))

    paddle.rect.width = new_width
    paddle.rect.centerx = center_x

    if paddle.rect.left < cfg.FIELD_LEFT:
        paddle.rect.left = cfg.FIELD_LEFT
    if paddle.rect.right > cfg.FIELD_RIGHT:
        paddle.rect.right = cfg.FIELD_RIGHT


def _scale_ball_speed(ball: Ball, factor: float) -> None:
    current_speed = math.hypot(ball.vx, ball.vy)
    if current_speed == 0:
        return

    target_speed = current_speed * factor
    target_speed = max(cfg.BALL_MIN_SPEED, min(cfg.BALL_MAX_SPEED, target_speed))

    scale = target_speed / current_speed
    ball.vx *= scale
    ball.vy *= scale


def apply_bonus(bonus_type: str, paddle: Paddle, balls: list[Ball], state: dict) -> None:
    if bonus_type == "extend":
        _resize_paddle(paddle, cfg.PADDLE_RESIZE_STEP)

    elif bonus_type == "shrink":
        _resize_paddle(paddle, -cfg.PADDLE_RESIZE_STEP)

    elif bonus_type == "speed_up":
        for ball in balls:
            _scale_ball_speed(ball, cfg.BALL_SPEED_MULTIPLIER)

    elif bonus_type == "speed_down":
        for ball in balls:
            _scale_ball_speed(ball, 1 / cfg.BALL_SPEED_MULTIPLIER)

    elif bonus_type == "multiball":
        for ball in balls[:]:
            clone = Ball(ball.rect.centerx, ball.rect.centery)
            clone.vx, clone.vy = -ball.vx, ball.vy
            balls.append(clone)

    elif bonus_type == "laser":
        paddle.laser = True

    elif bonus_type == "extra_life":
        state["lives"] = state.get("lives", 3) + 1
