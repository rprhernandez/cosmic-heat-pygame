import pygame
from classes.constants import WIDTH, HEIGHT
from key_bindings import bindings


def move_player(keys, player):
    left  = bindings.get("move_left")
    right = bindings.get("move_right")
    up    = bindings.get("move_up")
    down  = bindings.get("move_down")

    if keys[left]:
        if keys[up]:
            player.move_up_left()
        elif keys[down]:
            player.move_down_left()
        else:
            player.move_left()
    elif keys[right]:
        if keys[up]:
            player.move_up_right()
        elif keys[down]:
            player.move_down_right()
        else:
            player.move_right()
    elif keys[up]:
        player.move_up()
    elif keys[down]:
        player.move_down()
    else:
        player.stop()


def move_player_with_joystick(joystick, player):
    x_axis = joystick.get_axis(0)
    y_axis = joystick.get_axis(1)

    if abs(x_axis) > 0.1:
        new_x = player.rect.x + x_axis * player.speed
        if new_x < 0:
            new_x = 0
        elif new_x > WIDTH - player.rect.width:
            new_x = WIDTH - player.rect.width
        player.rect.x = new_x

    if abs(y_axis) > 0.1:
        new_y = player.rect.y + y_axis * player.speed
        if new_y < 0:
            new_y = 0
        elif new_y > HEIGHT - player.rect.height:
            new_y = HEIGHT - player.rect.height
        player.rect.y = new_y
