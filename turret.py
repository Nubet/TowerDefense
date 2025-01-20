import math
import pygame
from turret_data import TURRET_DATA
import const as c

# turret consts
ANIMATION_DELAY = 15  # Time between two frames in ms


class Turret(pygame.sprite.Sprite):
    """
    Represents a defensive turret in the game.

    The `Turret` class inherits from `pygame.sprite.Sprite`, allowing it to use
    sprite-related functionality, such as automatic group rendering and updates.

    Attributes:
        turret_type (str): The type of turret (e.g., "purple", "blue").
        turret_level (int): The current level of the turret (starts at 1).
        base_range (int): The base attack range of the turret.
        base_cooldown (int): The base cooldown time between attacks in ms.
        base_damage (int): The base damage dealt by the turret.
        range (int): The current attack range, which may differ due to upgrades.
        cooldown (int): The current cooldown time, affected by upgrades.
        damage (int): The current damage, affected by upgrades.
        last_shot (int): Timestamp of the last shot fired by the turret.
        selected (bool): Indicates if the turret is selected by the player.
        target (Enemy): The current target enemy.
        animation_steps (int): Number of animation frames for the turret's firing sequence.
        slow_amount (float): The slowing effect percentage applied by purple turrets.
        slow_duration (int): Duration of the slow effect in ms.
        mouse_tile_x (int): X-coordinate of the turret’s position on the tile grid.
        mouse_tile_y (int): Y-coordinate of the turret’s position on the tile grid.
        x (int): X-coordinate of the turret’s center.
        y (int): Y-coordinate of the turret’s center.
        sprite_sheets (list): List of sprite sheets for turret animations at each level.
        frame_index (int): Current animation frame index.
        animation_list (list): List of animation frames for the current turret level.
        update_time (int): Timestamp for updating the animation frame.
        angle (float): The current rotation angle of the turret.
        original_image (pygame.Surface): The base image of the turret.
        image (pygame.Surface): The rotated and scaled image of the turret.
        rect (pygame.Rect): The rectangle bounding the turret for rendering and collisions.
        tidal_active (bool): Indicates if a tidal upgrade is active.
        tidal_used (bool): Indicates if a tidal upgrade has been used this round.
        tidal_end_time (int): Timestamp when the tidal upgrade expires.
        TIDAL_MULTIPLIER (float): Multiplier applied during a tidal upgrade.
        TIDAL_DURATION (int): Duration of the tidal upgrade in ms.
        range_hitbox (pygame.Surface): Visual representation of the turret’s range.
        range_rect (pygame.Rect): Bounding rectangle for the range hitbox.

    Methods:
        create_range_hitbox():
            Creates or updates the visual representation of the turret’s range.

        load_images(sprite_sheet):
            Extracts animation frames from the given sprite sheet.

        update(enemy_group):
            Updates the turret logic each frame, including animation, targeting, and tidal upgrades.

        select_target(enemy_group):
            Searches for an enemy within the turret's range and attacks it.

        play_animation():
            Plays the firing animation when the turret attacks.

        upgrade():
            Permanently upgrades the turret's level and stats.

        tidally_upgrade():
            Activates a temporary tidal upgrade, boosting the turret's stats for a limited time.

        reset_tidal_upgrade():
            Resets the turret's stats after the tidal upgrade duration ends.

        draw(surface):
            Draws the turret and its range hitbox if selected.
    """
    def __init__(self, sprite_sheets, turret_type, mouse_tile_x, mouse_tile_y, x, y):
        """
         Initializes a turret with the specified type, position, and attributes.

               Args:
                   sprite_sheets (list): List of sprite sheets for turret animations at each level.
                   turret_type (str): The type of turret (e.g., "purple", "blue").
                   mouse_tile_x (int): X-coordinate of the turret’s position on the tile grid.
                   mouse_tile_y (int): Y-coordinate of the turret’s position on the tile grid.
                   x (int): X-coordinate of the turret’s center.
                   y (int): Y-coordinate of the turret’s center.

               Behavior:
                   - Loads base stats, such as range, cooldown, and damage, from `TURRET_DATA`.
                   - Initializes animation frames, targeting logic, and tidal upgrade parameters.
                   - Creates a visual representation of the turret’s attack range.
        """
        pygame.sprite.Sprite.__init__(self)

        # Turret type and level
        self.turret_type = turret_type
        self.turret_level = 1  # Start at level 1

        # Base stats from turret data (serve as temp copy when returning to normal stats when tidally upgrade ends)
        self.base_range = TURRET_DATA[self.turret_type][self.turret_level - 1].get("range")
        self.base_cooldown = TURRET_DATA[self.turret_type][self.turret_level - 1].get("cooldown")
        self.base_damage = TURRET_DATA[self.turret_type][self.turret_level - 1].get("damage")

        # Current stats (which may be modified by upgrades)
        self.range = self.base_range
        self.cooldown = self.base_cooldown
        self.damage = self.base_damage

        self.last_shot = pygame.time.get_ticks()
        self.selected = False
        self.target = None

        self.animation_steps = TURRET_DATA[self.turret_type][self.turret_level - 1].get("animation_steps")

        # Slow effect parameters (only for purple turret)
        if self.turret_type == "purple":
            self.slow_amount = TURRET_DATA[self.turret_type][self.turret_level - 1].get("slow_amount", 0)
            self.slow_duration = TURRET_DATA[self.turret_type][self.turret_level - 1].get("slow_duration", 0)
        else:
            self.slow_amount = 0
            self.slow_duration = 0

        # Position variables
        self.mouse_tile_x = mouse_tile_x
        self.mouse_tile_y = mouse_tile_y
        self.x = x
        self.y = y

        # Animation variables
        self.sprite_sheets = sprite_sheets
        self.frame_index = 0
        self.animation_list = self.load_images(self.sprite_sheets[self.turret_level - 1])
        self.update_time = pygame.time.get_ticks()

        # Initial image update
        self.angle = 90
        self.original_image = self.animation_list[self.frame_index]
        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 1)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        # Tidal Upgrade Variables
        self.tidal_active = False  # Indicates if a tidal upgrade is currently in effect
        self.tidal_used = False  # Indicates if this turret has used its tidal upgrade this round
        self.tidal_end_time = 0  # Timestamp when the tidal upgrade will expire
        self.TIDAL_MULTIPLIER = c.TIDAL_MULTIPLIER  # Multiplier applied during tidal upgrade
        self.TIDAL_DURATION = c.TIDAL_DURATION  # Duration in milliseconds (30 seconds)

        # Create the range hitbox
        self.create_range_hitbox()

    def create_range_hitbox(self):
        """
        Creates or updates the visual representation of the turret’s range.

            Behavior:
                - Draws a circle representing the turret’s range.
                - Displays a pink circle when a tidal upgrade is active and a gray circle otherwise.
        """
        self.range_hitbox = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        self.range_hitbox.fill((0, 0, 0, 0))
        if not self.tidal_active:  # pink range when turret is tidally upgraded
            pygame.draw.circle(self.range_hitbox, (128, 128, 128, 100), (self.range, self.range), self.range)
        else:
            pygame.draw.circle(self.range_hitbox, (255, 0, 255, 100), (self.range, self.range), self.range)
        self.range_hitbox.set_alpha(100)
        self.range_rect = self.range_hitbox.get_rect()
        self.range_rect.center = self.rect.center

    def load_images(self, sprite_sheet):
        """
        Extracts animation frames from the sprite sheet.

        Args:
            sprite_sheet (pygame.Surface): Sprite sheet containing animation frames.

        Returns:
            list: A list of Pygame surfaces, each representing an animation frame.
        """
        size = sprite_sheet.get_height()
        animation_list = []
        for i in range(self.animation_steps):
            frame = sprite_sheet.subsurface(i * size, 0, size, size)
            animation_list.append(frame)
        return animation_list

    def update(self, enemy_group):
        """
        Updates the turret logic every frame.

        Args:
            enemy_group (pygame.sprite.Group): Group of enemy sprites currently on the map.

        Behavior:
            - Checks if a tidal upgrade is active and resets it if expired.
            - Plays the turret's animation if it has a target.
            - Selects a new target if the turret is not currently targeting an enemy.
        """
        # Check if tidal upgrade is active and check if it has expired.
        if self.tidal_active and pygame.time.get_ticks() >= self.tidal_end_time:
            self.reset_tidal_upgrade()

        if self.target:
            self.play_animation()
        else:
            if pygame.time.get_ticks() - self.last_shot > self.cooldown:
                self.select_target(enemy_group)

    def select_target(self, enemy_group):
        """
          Searches for an enemy within the turret's range and then attacks it.

          Args:
              enemy_group (pygame.sprite.Group): Group of enemy sprites currently on the map.

          Behavior:
              - Iterates through all enemies in the group.
              - If an enemy is within range, it becomes the turret's target.
              - The turret inflicts damage and applies slow effects if applicable.
        """

        for enemy in enemy_group:
            if enemy.health > 0:
                x_dist = enemy.pos[0] - self.x
                y_dist = enemy.pos[1] - self.y
                dist = math.sqrt(x_dist**2 + y_dist**2)
                if dist < self.range:
                    self.target = enemy
                    self.angle = math.degrees(math.atan2(-y_dist, x_dist))
                    # Inflict damage on enemy
                    enemy.health -= self.damage
                    # Apply slow effect if appropriate
                    if self.turret_type == "purple" and self.slow_amount > 0 and self.slow_duration > 0:
                        enemy.apply_slow(self.slow_amount, self.slow_duration)
                    break

    def play_animation(self):
        """
        Plays the turret firing animation.

        Behavior:
            - Cycles through animation frames while the turret is firing.
            - Resets the animation and target when firing is complete.
        """
        self.original_image = self.animation_list[self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_DELAY:
            self.update_time = pygame.time.get_ticks()
            if self.frame_index < len(self.animation_list) - 1:
                self.frame_index += 1
            else:
                self.frame_index = 0
                self.last_shot = pygame.time.get_ticks()
                self.target = None

    def upgrade(self):
        """
        Permanently upgrades the turret's level and stats.

        Behavior:
            - Increases the turret's level and updates range, cooldown, damage based on `TURRET_DATA`.
            - Reloads animation frames and updates the range hitbox.
        """
        if self.turret_level < len(TURRET_DATA[self.turret_type]):
            self.turret_level += 1
            self.base_range = TURRET_DATA[self.turret_type][self.turret_level - 1].get("range")
            self.base_cooldown = TURRET_DATA[self.turret_type][self.turret_level - 1].get("cooldown")
            self.base_damage = TURRET_DATA[self.turret_type][self.turret_level - 1].get("damage")
            # Reset current stats to new base values
            self.range = self.base_range
            self.cooldown = self.base_cooldown
            self.damage = self.base_damage

            if self.turret_type == "purple":
                self.slow_amount = TURRET_DATA[self.turret_type][self.turret_level - 1].get("slow_amount", 0)
                self.slow_duration = TURRET_DATA[self.turret_type][self.turret_level - 1].get(
                    "slow_duration", 0
                )
            else:
                self.slow_amount = 0
                self.slow_duration = 0

            self.animation_list = self.load_images(self.sprite_sheets[self.turret_level - 1])
            self.original_image = self.animation_list[self.frame_index]
            self.create_range_hitbox()
            print("Turret upgraded permanently.")

    def tidally_upgrade(self):
        """
        Activate a temporary tidal upgrade.

        Behavior:
          - Applies a given in const.py x multiplier to stats.
          - Lasts for a fixed duration of x seconds (default 30 seconds)
          - Can be applied only once per round.
        """
        if not self.tidal_used and not self.tidal_active:
            # Apply the multiplier only once
            self.range = int(self.base_range * self.TIDAL_MULTIPLIER)
            self.damage = int(self.base_damage * self.TIDAL_MULTIPLIER)

            self.tidal_active = True
            self.tidal_used = True
            self.tidal_end_time = pygame.time.get_ticks() + self.TIDAL_DURATION
            self.create_range_hitbox()
            print(f"Tidal upgrade applied  turret at ({self.x}, {self.y}) until {self.tidal_end_time}ms.")

    def reset_tidal_upgrade(self):
        """
        Resets turret stats after a tidal upgrade expires.

        Behavior:
            - Restores range, damage, and cooldown to base values.
            - Updates the range hitbox to reflect the normal range.
        """
        self.range = self.base_range
        self.damage = self.base_damage
        self.cooldown = self.base_cooldown
        self.tidal_active = False
        self.tidal_end_time = 0
        self.create_range_hitbox()
        print(f"Tidal upgrade expired for turret at ({self.x}, {self.y}).")

    def draw(self, surface):
        """
        Draws the turret and its range hitbox if selected.

        Args:
            surface (pygame.Surface): The surface to draw the turret and hitbox on.

        Behavior:
            - Rotates and draws the turret image on the screen.
            - Draws a translucent circle representing the turret's range if selected.
        """
        # turret images default orientation points upward so we subtract 90
        # because the rotation angle is measured from the positive x-axis.
        self.image = pygame.transform.rotozoom(self.original_image, self.angle - 90, 1)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        surface.blit(self.image, self.rect)
        if self.selected:
            surface.blit(self.range_hitbox, self.range_rect)
