import pygame

from .constants import WIDTH, HEIGHT


class Player:

    def __init__(self):
        self.rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 100, 100, 100)
        self.speed = 10
        self.image = pygame.image.load('images/player.png').convert_alpha()
        self.original_image = self.image.copy()
        self.direction = 'down'
        self._cached_hp_percent = 100
        self._cached_damaged_image = None
        self._cached_damaged_image_flipped = None

    def _get_damage_state(self, hp_percent):
        """Return damage state: 0=healthy, 1=light, 2=moderate, 3=heavy, 4=critical."""
        if hp_percent > 75:
            return 0
        elif hp_percent > 50:
            return 1
        elif hp_percent > 25:
            return 2
        elif hp_percent > 10:
            return 3
        else:
            return 4

    def _apply_damage_overlay(self, base_image, hp_percent):
        """Apply visual damage effects based on HP percentage."""
        state = self._get_damage_state(hp_percent)
        if state == 0:
            return base_image.copy()

        result = base_image.copy()
        w, h = result.get_size()

        # Tint colors: progressively more red/orange as damage increases
        tint_colors = [
            None,                    # 0: no tint
            (255, 200, 150, 30),     # 1: light damage - slight orange tint
            (255, 150, 100, 60),     # 2: moderate - more orange
            (255, 100, 50, 90),      # 3: heavy - orange-red
            (255, 50, 30, 120),      # 4: critical - deep red
        ]

        # Apply color tint overlay
        tint = tint_colors[state]
        if tint:
            tint_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            tint_surface.fill(tint)
            result.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # Add reddish overlay
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((tint[0], tint[1], tint[2], tint[3] // 2))
            result.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Add damage marks (dark spots) for moderate+ damage
        if state >= 2:
            damage_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            num_marks = (state - 1) * 3

            import random
            # Use a seed based on state so marks are consistent per damage level
            rng = random.Random(42 + state)

            for _ in range(num_marks):
                x = rng.randint(w // 4, 3 * w // 4)
                y = rng.randint(h // 4, 3 * h // 4)
                radius = rng.randint(2, 4 + state)
                alpha = 80 + state * 20
                pygame.draw.circle(damage_surface, (40, 20, 10, alpha), (x, y), radius)

            result.blit(damage_surface, (0, 0))

        # Add smoke/char effect for heavy+ damage
        if state >= 3:
            smoke_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            rng = random.Random(99 + state)
            for _ in range(state * 2):
                x = rng.randint(0, w - 1)
                y = rng.randint(0, h - 1)
                radius = rng.randint(3, 6 + state)
                pygame.draw.circle(smoke_surface, (30, 30, 30, 40 + state * 10), (x, y), radius)
            result.blit(smoke_surface, (0, 0))

        return result

    def get_display_image(self, hp_percent):
        """Return the appropriate image based on current HP percentage."""
        # Clamp hp_percent
        hp_percent = max(0, min(100, hp_percent))

        # Check if we need to regenerate the cached damaged image
        current_state = self._get_damage_state(hp_percent)
        cached_state = self._get_damage_state(self._cached_hp_percent)

        if current_state != cached_state or self._cached_damaged_image is None:
            self._cached_hp_percent = hp_percent
            self._cached_damaged_image = self._apply_damage_overlay(self.original_image, hp_percent)
            self._cached_damaged_image_flipped = pygame.transform.flip(self._cached_damaged_image, True, False)

        # Return the correct orientation based on direction
        if self.direction == 'left' or self.direction == 'up_left' or self.direction == 'down_left':
            return self._cached_damaged_image_flipped
        else:
            return self._cached_damaged_image

    def move_left(self):
        if self.rect.left > 0:
            self.rect.x -= self.speed
            self.direction = 'left'
            self.image = pygame.transform.flip(self.original_image, True, False)

    def move_right(self):
        if self.rect.right < WIDTH:
            self.rect.x += self.speed
            self.direction = 'right'
            self.image = self.original_image

    def move_up(self):
        if self.rect.top > 0:
            self.rect.y -= self.speed
            self.direction = 'up'

    def move_down(self):
        if self.rect.bottom < HEIGHT:
            self.rect.y += self.speed
            self.direction = 'down'

    def move_up_left(self):
        if self.rect.top > 0 and self.rect.left > 0:
            self.rect.x -= self.speed
            self.rect.y -= self.speed
            self.direction = 'up_left'

    def move_up_right(self):
        if self.rect.top > 0 and self.rect.right < WIDTH:
            self.rect.x += self.speed
            self.rect.y -= self.speed
            self.direction = 'up_right'

    def move_down_left(self):
        if self.rect.bottom < HEIGHT and self.rect.left > 0:
            self.rect.x -= self.speed
            self.rect.y += self.speed
            self.direction = 'down_left'

    def move_down_right(self):
        if self.rect.bottom < HEIGHT and self.rect.right < WIDTH:
            self.rect.x += self.speed
            self.rect.y += self.speed
            self.direction = 'down_right'

    def stop(self):
        pass

    def stop_left(self):
        pass

    def stop_right(self):
        pass

    def stop_up(self):
        pass

    def stop_down(self):
        pass