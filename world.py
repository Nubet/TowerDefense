import pygame
import random
from enemy_data import WAVE_ENEMY_DATA
import const as c


class World:
    """
       Represents the game world, including the tile map, waypoints, and enemies.

       Attributes:
           level (int): Current level of the game.
           health (int): Player's health points.
           money (int): Player's money.
           tile_map (list): List of tile data for the map background.
           waypoints (list): List of waypoints (coordinates) for enemy paths.
           level_data (dict): Data for the current level, typically loaded from a Tiled .tmj file.
           image (pygame.Surface): Image of the map background.
           enemy_list (list): List of enemies to spawn for the current wave.
           spawned_enemies (int): Number of enemies that have been spawned.
           killed_enemies (int): Number of enemies that have been killed.
           missed_enemies (int): Number of enemies that reached the end without being killed.

       Methods:
           __init__(world_data, map_image):
               Initializes the game world with level data and map image.

           process_data():
               Processes the level data to extract tile map and waypoints.

           process_waypoints(data):
               Extracts individual sets of x and y coordinates from waypoint data.

           process_enemies():
               Populates the enemy list with enemies to spawn in the current wave.

           draw(surface):
               Draws the map image onto the given surface.

           is_wave_completed():
               Checks if the wave is completed by comparing the number of killed+missed enemies to the total amount.

           reset_values():
               Resets values for a new wave, including enemy lists and counters.
       """

    def __init__(self, world_data, map_image):
        """
        Initializes the game world with level data and map image.

        Args:
            world_data (dict): Data for the current level, including tile map and waypoints.
            map_image (pygame.Surface): Image of the map background.
        """
        self.level = 1
        self.health = c.HEALTH
        self.money = c.MONEY
        self.tile_map = []
        self.waypoints = []
        self.level_data = world_data
        self.image = map_image
        self.enemy_list = []
        self.spawned_enemies = 0
        self.killed_enemies = 0
        self.missed_enemies = 0

    def process_data(self):
        """
        Processes the level data to extract relevant information, such as the tile map and waypoints.

        For the tile map:
        - Extracts data from the "Background" layer.

        For the waypoints:
        - Parses the "waypoints" layer, extracting a list of waypoints for enemy movement.
        """
        for layer in self.level_data[
            "layers"
        ]:  # getting into layers list from level.tmj (while using Tiled, tilemap have to be created as .csv format)
            if layer["name"] == "Background":  # processing all tiles
                self.tile_map = layer["data"]
                # print("\n ",self.tile_map) # return one long list e.g. [7, 7, 7, 7, 8, 6, 7, 7, 12, 12, 12, 12, .... ]
            elif layer["name"] == "waypoints":  # processing waypoints
                for obj in layer["objects"]:
                    waypoint_data = obj["polyline"]
                    print(
                        "\n ", waypoint_data
                    )  # so printed data is list that have bunch of dictionaries inside it so we need to parse it more
                    self.process_waypoints(waypoint_data)

    def process_waypoints(self, data):
        """
           Iterate through waypoints to extract individual sets of x and y coordinates.

           Args:
               data (list): List of dictionaries containing waypoint coordinates.
           """
        # print("waypoints: ")
        for point in data:
            # print(point)
            temp_x = point["x"]
            temp_y = point["y"]
            # print((temp_x, temp_y))
            self.waypoints.append([temp_x, temp_y])

    def process_enemies(self):
        """
         Populates the enemy list for the current wave based on the `WAVE_ENEMY_DATA`.

         Function appends each enemy type to the `self.enemy_list` based on the spawn count from configuration file
         Then it randomizes the `self.enemy_list` to shuffle the order of enemy spawning.
         """
        enemies = WAVE_ENEMY_DATA[self.level - 1]
        for enemy_type in enemies:
            enemies_to_spawn = enemies[enemy_type]
            for enemy in range(enemies_to_spawn):
                # print(enemy_type)
                self.enemy_list.append(enemy_type)
            # now randomize the list to shuffle the enemies
            random.shuffle(self.enemy_list)

    def draw(self, surface):
        """
         Draws the map image onto the given surface.

         Args:
         surface (pygame.Surface): The surface where the map image will be drawn.
        """
        surface.blit(self.image, (0, 0))

    def is_wave_completed(self):
        """
         Checks if the wave is completed.

         Returns:
         bool: True if the wave is completed, False otherwise.
        """
        return (self.killed_enemies + self.missed_enemies) == len(self.enemy_list)

    def reset_values(self):
        """
         Resets values to prepare for a new wave.
        """
        self.enemy_list = []
        self.level += 1
        self.spawned_enemies = 0
        self.killed_enemies = 0
        self.missed_enemies = 0
