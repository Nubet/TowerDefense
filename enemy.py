import pygame
import math
from pygame.math import Vector2
from enemy_data import ENEMY_DATA
import const as c


# Enemy class inherits from pygame.sprite.Sprite thanks to this we inherit all the functionality,
# methods and attributes from the Sprite class. So it does not matter how many enemies I create,
# by calling "enemy_group.draw(screen)" it will automatically draw all of them on the screen


class Enemy(pygame.sprite.Sprite):
    """
        Represents an enemy unit in the game.

        The `Enemy` class inherits from `pygame.sprite.Sprite`, allowing it to use
        all sprite-related functionality, such as automatic group rendering and updating.

        Attributes:
            enemy_type (str): The type of the enemy (e.g., "orc", "goblin").
            waypoints (list): List of waypoints the enemy will follow.
            pos (Vector2): Current position of the enemy as a vector.
            target_waypoint (int): Index of the current target waypoint.
            health (float): Current health of the enemy.
            max_health (float): Maximum health of the enemy.
            speed (float): Current movement speed of the enemy.
            original_speed (float): Base movement speed of the enemy.
            damage_inflicted (int): Amount of damage the enemy inflicts upon reaching the endpoint.
            angle (float): Current angle of the enemy's rotation in degrees.
            is_slowed (bool): Indicates if the enemy is slowed.
            slow_timer (int): Timestamp for when the slow effect will end.
            image (pygame.Surface): Current image of the enemy, potentially rotated.
            rect (pygame.Rect): Rectangle bounding the enemy for rendering and collision.
            health_multiplier (float): Multiplier applied to the enemy's health based on difficulty.
            speed_multiplier (float): Multiplier applied to the enemy's speed based on difficulty.

        Methods:
            __init__(enemy_type, waypoints, images, difficulty="normal"):
                Initializes an enemy with specified attributes and difficulty.

            update(world):
                Updates the enemy's state, including movement, rotation, health checks, and slow effects.

            move(world):
                Moves the enemy towards its next waypoint or inflicts damage if it reaches the endpoint.

            rotate():
                Rotates the enemy's image to face the next waypoint.

            check_if_alive(world):
                Checks if the enemy is alive and handles its death, including rewards for the player.

            draw_health_bar(surface):
                Draws a health bar above the enemy to indicate its remaining health.

            apply_slow(slow_amount, slow_duration):
                Applies a slowing effect to the enemy, reducing its speed temporarily.

            update_slow_effect():
                Updates the slow effect based on the timer and resets speed if the effect has ended.
        """
    def __init__(self, enemy_type, waypoints, images, difficulty="normal"):
        """
              Initializes an enemy with specified attributes and difficulty.

              Args:
                  enemy_type (str): The type of enemy (e.g., "strong", "elite").
                  waypoints (list): List of (x, y) coordinates representing the enemy's path.
                  images (dict): Dictionary of enemy type to corresponding Pygame images.
                  difficulty (str, optional): Difficulty level ("easy", "normal", "hard"). Default is "normal".

              Attributes Initialized:
                  - Enemy health, speed, and damage are set based on the type and difficulty multipliers.
                  - The enemy's image is prepared, and its position is set to the starting waypoint.
                  - The enemy is initialized without any slow effect.
        """
        pygame.sprite.Sprite.__init__(self)
        self.enemy_type = enemy_type
        # using waypoints list now we can extract pos var (which is starting position of enemy)
        # and its gonna be 0 index from list
        self.waypoints = waypoints
        self.pos = Vector2(
            self.waypoints[0]   # Starting position of the enemy
        )  # defining pos as vector gives as more math functionalities so it will make following path much simpler
        self.target_waypoint = (
            1  # in 'def move' function we will use this var as argument to self.waypoints[]
        )

        # Difficulty multipliers
        if difficulty == "easy":
            self.health_multiplier = 0.75
            self.speed_multiplier = 0.9
        elif difficulty == "hard":
            self.health_multiplier = 1.25
            self.speed_multiplier = 1.2
        else:
            self.health_multiplier = 1.0
            self.speed_multiplier = 1.0

        # Enemy attributes
        self.health = ENEMY_DATA[self.enemy_type]["health"] * self.health_multiplier
        self.max_health = self.health  # MAX health in bar
        self.original_speed = ENEMY_DATA[self.enemy_type]["speed"] * self.speed_multiplier
        self.speed = self.original_speed  # Current speed, can be modified by slow effects
        self.damage_inflicted = ENEMY_DATA[self.enemy_type]["damage_inflicted"]
        self.angle = 0  # Starting angle

        # Image and rect setup
        self.original_image = images[self.enemy_type]
        self.image = pygame.transform.rotate(
            self.original_image, self.angle
        )  # rotating original image by given angle
        self.rect = self.image.get_rect()
        self.rect.center = self.pos

        # Attributes for slow effect
        self.is_slowed = False
        self.slow_timer = 0

    def update(self, world):
        """
            Updates the enemy's state, including movement, rotation, health checks, and slow effects.

            Args:
                world (World): The current game world, used for health deduction and tracking.
            """
        self.move(world)
        self.rotate()
        self.check_if_alive(world)
        self.update_slow_effect()

    def move(self, world):
        """
               Moves the enemy towards its next waypoint or inflicts damage if it reaches the endpoint.

               Args:
                   world (World): The current game world, used for health deduction and tracking missed enemies.

               Behavior:
                   - The enemy moves towards the current target waypoint.
                   - If the enemy reaches the last waypoint, it deducts health from the world and removes itself.
                   - The movement vector is normalized to ensure consistent speed.
                   - The target waypoint updates when the enemy reaches the current one.
        """
        # define a target waypoint
        if self.target_waypoint < len(
            self.waypoints
        ):  # as long as we have remaining waypoints in list we keep setting new targets
            self.target = Vector2(self.waypoints[self.target_waypoint])
            self.movement = self.target - self.pos  # distance between 2 waypoints
        else:  # enemy has reached to the end of the path
            world.health -= self.damage_inflicted
            world.missed_enemies += 1
            self.kill()  # kill is method inherited from pygame.sprite.Sprite
            return

        # calculate distance to target
        dist = self.movement.length()

        # check if remaining distance is greater than enemy speed
        if dist >= self.speed:  # prevent overshooting the target
            # normalizing returns a vector with the same direction but length 1
            # so this function handles the trigonometry, so output [0.948683, 0.316228] means that if we want to enemy
            # to follow the path we need to move along it by 0.948683 this many pixels, and move it down 0.316228 pixels
            self.pos += self.movement.normalize() * self.speed
        else:
            if dist != 0:  # 'dist' is zero, it means the enemy has reached perfectly to the target
                self.pos += (
                    self.movement.normalize() * dist
                )  # it will move only a little bit, so it will end perfectly aligned
                # we are changing the target that enemy is following, otherwise self.movement
                # would ended as vector 0 which cant be normalize()
            self.target_waypoint += 1

        # self.rect.center = self.pos

    def rotate(self):
        """
        Rotates the enemy to face its current movement direction.

        The rotation is calculated using the angle between the enemy's position and its next waypoint.
        """
        #
        if self.target_waypoint < len(self.waypoints):
            dist = self.target - self.pos
            # use distance to calc angle
            self.angle = math.degrees(
                math.atan2(-dist[1], dist[0])
            )  # we invert y-coord because in pygame, the y-coord increases downwards, in contrary to Cartesian system
            # rotate image and update rectangle
            self.image = pygame.transform.rotate(
                self.original_image, self.angle
            )  # we are operating on 'original_image' to avoid destroying quality of our image due to rotations
            self.rect = self.image.get_rect()
            self.rect.center = self.pos

    def check_if_alive(self, world):
        """
        Checks if the enemy is alive and handles its death.

        Args:
            world (World): The current game world, used for tracking killed enemies and awarding rewards.

        Behavior:
            - If the enemy's health is zero or less, it is removed, and the player is rewarded with money.
        """
        if self.health <= 0:
            world.killed_enemies += 1
            world.money += ENEMY_DATA[self.enemy_type]["kill_reward"]
            self.kill()

    def draw_health_bar(self, surface):
        """
        Draw the enemy's health bar above the enemy.

        Args:
            surface (pygame.Surface): The surface to draw the health bar on.
        """
        bar_width = 40
        bar_height = 5
        health_ratio = self.health / self.max_health
        bar_x = self.rect.centerx - bar_width // 2  # Centered horizontally relative to the enemy
        bar_y = self.rect.top + 10

        # Change color based on slow effect
        if self.is_slowed:
            bar_color = (0, 0, 255)  # Blue
        else:
            bar_color = (0, 255, 0)  # Green for normal

        # Draw health bar background (red)
        pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # Draw current health
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, bar_width * health_ratio, bar_height))

    def apply_slow(self, slow_amount, slow_duration):
        """
        Apply a slow effect to the enemy.

        Args:
            slow_amount (float): The percentage reduction in speed (e.g., 0.2 for 20% reduction).
            slow_duration (int): Duration of the slow effect in milliseconds.

        """
        if not self.is_slowed:
            self.is_slowed = True
            self.speed = self.original_speed * (1 - slow_amount)
            self.slow_timer = pygame.time.get_ticks() + slow_duration
            print(f"Enemy slowed by {slow_amount * 100}% for {slow_duration}ms.")

    def update_slow_effect(self):
        """Update the slow effect based on the timer."""
        if self.is_slowed and pygame.time.get_ticks() > self.slow_timer:
            self.is_slowed = False
            self.speed = self.original_speed
            print("Enemy slow effect has ended.")
