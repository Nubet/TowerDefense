import os
import pygame
from pygame.math import Vector2
import const as c
from enemy import Enemy
from world import World
from turret import Turret
from button import Button
from turret_data import TURRET_DATA
from enemy_data import WAVE_ENEMY_DATA
import json


class Game:
    """
       Represents the main Tower Defense game.

       Attributes:
           ROWS (int): Number of rows in the tile map.
           COLS (int): Number of columns in the tile map.
           TILE_SIZE (int): Size of each tile in pixels.
           SCREEN_WIDTH (int): Width of the game screen.
           SCREEN_HEIGHT (int): Height of the game screen.
           SIDE_PANEL (int): Width of the side panel.
           FPS (int): Frames per second.
           state (str): Current state of the game (menu, game, game_over).
           selected_map (int): Currently selected map.
           difficulties (list): List of difficulty levels.
           current_difficulty_index (int): Index of the currently selected difficulty.
           selected_difficulty (str): Name of the currently selected difficulty.
           MAX_LEVELS (int): Maximum number of levels.
           wave_started (bool): Whether the wave has started.
           last_enemy_spawn (int): Timestamp of the last enemy spawn.
           placing_turrets (bool): Whether the player is placing turrets.
           selected_turret (Turret): Currently selected turret.
           turret_buy_costs (dict): Cost of buying turrets by type.
           occupied_tiles (dict): Dictionary of all occupied tiles.
           world (World): Instance of the game world.
           display_surface (pygame.Surface): Main display surface for the game.
           screen (pygame.Surface): Internal game screen surface.
           enemy_group (pygame.sprite.Group): Group of enemy sprites.
           turret_group (pygame.sprite.Group): Group of turret sprites.
           turret_spritesheets (list): Sprite sheets for standard turrets.
           camo_turret_spritesheets (list): Sprite sheets for camo turrets.
           purple_turret_spritesheets (list): Sprite sheets for purple turrets.

       Methods:
           __init__():
               Initializes the game, assets, and states.

           load_menu_images():
               Loads and prepares map images for the menu.

           load_images():
               Loads all necessary game assets, including turrets and enemies.

           load_fonts():
               Loads fonts for displaying text on the screen.

           load_level_data(map_number):
               Loads the JSON data for the selected map.

           create_buttons():
               Creates all necessary game buttons.

           draw_text(text, font, text_col, x, y):
               Draws text on the screen.

           create_turret(mapped_mouse_pos):
               Creates a turret at the specified position.

           select_turret(mapped_mouse_pos):
               Selects a turret at the specified position.

           reset_occupied_tiles():
               Clears all occupied tiles.

           restart_level():
               Restarts the game level.

           handle_events():
               Handles all user inputs and events.

           update():
               Updates the game logic.

           skip_wave():
               Skips the current wave and penalizes the player's health.

           draw_menu():
               Draws the map selection menu.

           draw_game_over():
               Draws the game over screen.

           draw_game():
               Draws all elements of the game.

           draw():
               Draws the appropriate screen based on the current game state.

           run():
               Runs the main game loop.

           map_mouse_cursor(pos):
               Maps the mouse position from the display surface to internal screen coordinates.
       """
    def __init__(self):
        """
        Initializes the game, assets, and states.

        Behavior:
            - Sets up the Pygame environment.
            - Loads assets, fonts, and buttons.
            - Initializes game variables, including tile maps, states, and groups.
         """
        # Initialize Pygame
        os.environ["SDL_WINDOWS_DPI_AWARENESS"] = "permonitorv2"  # for proper scaling
        pygame.init()
        self.clock = pygame.time.Clock()

        # Tile map variables
        self.ROWS = c.ROWS
        self.COLS = c.COLS
        self.TILE_SIZE = c.TILE_SIZE

        # Screen settings
        self.SCREEN_WIDTH = c.TILE_SIZE * c.COLS
        self.SCREEN_HEIGHT = c.TILE_SIZE * c.ROWS
        self.SIDE_PANEL = 400
        self.FPS = c.FPS  # 60

        initial_window_size = c.RESOLUTION
        self.display_surface = pygame.display.set_mode(initial_window_size, pygame.RESIZABLE)

        # Internal game surface
        self.screen = pygame.Surface((self.SCREEN_WIDTH + self.SIDE_PANEL, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Tower Defense - Norbert Fila")

        # Game states
        self.state = "menu"  # Possible states: menu, game, game_over

        # Menu variables
        self.menu_map_images = []
        self.menu_map_rects = []  # Rects defining the position of each map image
        self.selected_map = None
        self.load_menu_images()

        # Difficulty settings
        self.difficulties = ["easy", "normal", "hard"]
        self.current_difficulty_index = 1  # Start with 'normal'
        self.selected_difficulty = self.difficulties[self.current_difficulty_index]

        # Game variables
        self.MAX_LEVELS = len(WAVE_ENEMY_DATA)
        self.game_status = 0  # 1 for win, -1 for loss
        self.wave_started = False
        self.last_enemy_spawn = pygame.time.get_ticks()
        self.placing_turrets = False
        self.selected_turret = None
        self.placement_message = ""  # Message for user feedback in right corner
        self.message_timer = 0
        self.current_turret_type = "standard"

        # Turret buy costs
        self.turret_buy_costs = c.turret_buy_costs  # "standard": 200, "camo": 200, "purple": 500

        # Define colors
        self.BACKGROUND_COLOR = (255, 255, 255)
        self.SIDE_PANEL_COLOR = (50, 50, 50)  # Dark Grey

        # Load assets
        self.load_images()
        self.load_fonts()

        # Create sprite groups
        self.enemy_group = pygame.sprite.Group()
        self.turret_group = pygame.sprite.Group()

        # Create buttons
        self.create_buttons()

        # Dictionary of all occupied tiles
        self.occupied_tiles = {}

        # Initialize world as None
        self.world = None

    def load_menu_images(self):
        """
        Loads and prepares map images for the menu.

        Behavior:
            - Loads images for each map and creates bordered versions.
            - Calculates their positions for rendering in the menu.
        """
        # List of map names available in the menu
        maps = ["MAP1", "MAP2", "MAP3"]
        map_image_size = (350, 350)
        full_image_size = (
            map_image_size[0] + 8,
            map_image_size[1] + 8,
        )  # 358x358 pixels (4 pixels border on each side)

        # Calculate the total width occupied by all map images and their spacing
        spacing = 100
        total_width = len(maps) * full_image_size[0] + (len(maps) - 1) * spacing  # 3 maps + 2 gaps

        # Calculate the starting X position to center the group of maps horizontally
        available_width = self.SCREEN_WIDTH + self.SIDE_PANEL
        start_x = (available_width - total_width) // 2 + full_image_size[0] // 2
        y_position = self.SCREEN_HEIGHT // 2

        # Iterate over each map with its corresponding index
        for map_index in range(len(maps)):
            map_name = maps[map_index]
            map_image_path = f"levels/{map_name}/{map_name.lower()}.png"  # e.g. 'levels/MAP1/map1.png'

            # Scaling map image
            image = pygame.image.load(map_image_path).convert_alpha()
            image = pygame.transform.scale(image, map_image_size)

            bordered_image = pygame.Surface(full_image_size, pygame.SRCALPHA)
            bordered_image.fill((0, 0, 0, 0))  # Transparent

            # Draw a white border around the image
            pygame.draw.rect(
                bordered_image,
                (255, 255, 255),
                (
                    0,
                    0,
                    full_image_size[0],
                    full_image_size[1],
                ),  # Full size of the bordered image
                4,  # Border thickness in pixels
            )
            bordered_image.blit(image, (4, 4))

            # Add the bordered image to the list of menu map images for rendering
            self.menu_map_images.append(bordered_image)

            # Define the horizontal spacing between each map image
            x_spacing = spacing + full_image_size[0]  # 100 pixels between maps + width of one map

            # Calculate the X position for the current map based on its index
            x_position = start_x + map_index * x_spacing

            rect = bordered_image.get_rect()
            rect.center = (x_position, y_position)

            # Add the position rectangle to the list of menu map rectangles
            self.menu_map_rects.append(rect)

    def load_images(self):
        """
        Loads all necessary game assets.

        Behavior:
            - Loads images for enemies, turrets, and buttons.
            - Creates sprite sheets for turrets at different levels.
        """
        # Load map image
        self.map_image = pygame.image.load("levels/MAP3/map3.png").convert_alpha()

        # Load enemy images
        self.enemy_images = {
            "weak": pygame.image.load("assets/images/enemies/enemy_1.png").convert_alpha(),
            "medium": pygame.image.load("assets/images/enemies/enemy_2.png").convert_alpha(),
            "strong": pygame.image.load("assets/images/enemies/enemy_3.png").convert_alpha(),
            "elite": pygame.image.load("assets/images/enemies/enemy_4.png").convert_alpha(),
        }

        # Load turret cursor images
        self.cursor_standard = pygame.image.load(
            "assets/images/turrets/standard/cursor_turret.png"
        ).convert_alpha()
        self.cursor_camo_turret = pygame.image.load(
            "assets/images/turrets/camo/camo_cursor_turret.png"
        ).convert_alpha()
        self.cursor_purple_turret = pygame.image.load(
            "assets/images/turrets/purple/purple_cursor_turret.png"
        ).convert_alpha()

        # Loading Sprite sheets #

        # Standard Turret sprite sheets
        self.turret_spritesheets = []
        for x in range(1, 5):  # 4 levels
            turret_sheet = pygame.image.load(f"assets/images/turrets/standard/turret_{x}.png").convert_alpha()
            self.turret_spritesheets.append(turret_sheet)

        # Camo Turret sprite sheets
        self.camo_turret_spritesheets = []
        for x in range(1, 5):  # 4 levels
            turret_sheet = pygame.image.load(f"assets/images/turrets/camo/turret_{x}.png").convert_alpha()
            self.camo_turret_spritesheets.append(turret_sheet)

        # Purple Turret sprite sheets
        self.purple_turret_spritesheets = []
        for x in range(1, 5):  # 4 levels
            turret_sheet = pygame.image.load(f"assets/images/turrets/purple/turret_{x}.png").convert_alpha()
            self.purple_turret_spritesheets.append(turret_sheet)

        # Load button images
        self.buy_turret_image = pygame.image.load(
            "assets/images/turrets/standard/cursor_turret.png"
        ).convert_alpha()
        self.camo_buy_turret_image = pygame.image.load(
            "assets/images/turrets/camo/camo_cursor_turret.png"
        ).convert_alpha()
        self.buy_purple_turret_image = pygame.image.load(
            "assets/images/turrets/purple/purple_cursor_turret.png"
        ).convert_alpha()
        self.cancel_image = pygame.image.load("assets/images/buttons/cancel.png").convert_alpha()
        self.upgrade_image = pygame.image.load("assets/images/buttons/upgrade_turret.png").convert_alpha()
        self.tidal_upgrade_image = pygame.image.load(
            "assets/images/buttons/tidally_upgrade_turret.png"
        ).convert_alpha()
        self.begin_image = pygame.image.load("assets/images/buttons/begin.png").convert_alpha()
        self.restart_image = pygame.image.load("assets/images/buttons/restart.png").convert_alpha()
        self.sell_image = pygame.image.load("assets/images/buttons/sell.png").convert_alpha()
        self.back_to_menu_image = pygame.image.load("assets/images/buttons/back_to_menu.png").convert_alpha()

        # Load difficulty images
        self.difficulty_images = []
        difficulty_image_paths = {
            "easy": "assets/images/buttons/easy.png",
            "normal": "assets/images/buttons/normal.png",
            "hard": "assets/images/buttons/hard.png",
        }
        for difficulty in self.difficulties:
            image = pygame.image.load(difficulty_image_paths[difficulty]).convert_alpha()
            self.difficulty_images.append(image)

    def load_fonts(self):
        """
        Loads fonts for displaying text on the screen.

        Behavior:
            - Sets up small, medium, and large font styles.
        """
        self.text_font = pygame.font.SysFont("Consolas", 24, bold=True)
        self.small_text_font = pygame.font.SysFont("Consolas", 20, bold=True)
        self.large_font = pygame.font.SysFont("Consolas", 36)

    def load_level_data(self, map_number):
        """
        Loads the JSON data for the selected map.

        Args:
            map_number (int): The number of the selected map.

        Behavior:
            - Loads the .tmj file containing map data (in json format) and verifies its dimensions.
            - Prepares the map image for rendering.
        """
        tmj_path = f"levels/MAP{map_number}/map{map_number}.tmj"  # e.g., 'levels/MAP3/map3.tmj'
        png_path = f"levels/MAP{map_number}/map{map_number}.png"

        # Open and load the JSON data for the map
        with open(tmj_path) as file:
            self.world_data = json.load(file)

        print(f"World data for MAP{map_number}:", self.world_data)

        # Load the map image using Pygame
        self.map_image = pygame.image.load(png_path).convert_alpha()

        # Verify tile map length
        tile_map_length = len(self.world_data["layers"][0]["data"])
        expected_length = self.ROWS * self.COLS
        # print(f"[DEBUG] Tile map length: {tile_map_length}, Expected: {expected_length}")
        if tile_map_length != expected_length:
            print("Error: Tile map size does not match ROWS x COLS.")

    def create_buttons(self):
        """Create all necessary buttons."""
        self.turret_button = Button(self.SCREEN_WIDTH + 30, 120, self.buy_turret_image, True)
        self.camo_turret_button = Button(self.SCREEN_WIDTH + 200, 120, self.camo_buy_turret_image, True)
        self.purple_turret_button = Button(self.SCREEN_WIDTH + 110, 120, self.buy_purple_turret_image, True)
        self.cancel_button = Button(self.SCREEN_WIDTH + 105, 230, self.cancel_image, True)
        self.upgrade_button = Button(self.SCREEN_WIDTH + 30, 230, self.upgrade_image, True)
        self.tidal_upgrade_button = Button(self.SCREEN_WIDTH + 100, 300, self.tidal_upgrade_image, True)
        self.begin_button = Button(self.SCREEN_WIDTH + 200, 730, self.begin_image, True)
        self.restart_button = Button(self.SCREEN_WIDTH // 2 + 120, 480, self.restart_image, True)
        self.sell_button = Button(self.SCREEN_WIDTH + 240, 230, self.sell_image, True)
        self.back_to_menu_button = Button(self.SCREEN_WIDTH + 200, 800, self.back_to_menu_image, True)
        self.difficulty_button = Button(
            self.SCREEN_WIDTH // 2 + 150, 780, self.difficulty_images[1], True
        )  # 'normal' as default
        self.skip_button = Button(
            self.SCREEN_WIDTH + 30,
            800,
            pygame.image.load("assets/images/buttons/skip.png").convert_alpha(),
            True,
        )

    def draw_text(self, text, font, text_col, x, y):
        """Draws text on the screen."""
        img = font.render(text, True, text_col)
        self.screen.blit(img, (x, y))
        return self.draw_text

    def create_turret(self, mapped_mouse_pos):
        """
        Creates a turret at the given position.

        Args:
            mapped_mouse_pos (tuple): The mapped position of the mouse click.

        Returns:
            bool: True if the turret was successfully placed, False otherwise.

        Behavior:
            - Checks if the tile is valid and unoccupied.
            - Places a turret and deducts the cost from the player's money.
        """
        # Convert the pixel position of the mouse click into grid coordinates
        mouse_tile_x = int(mapped_mouse_pos[0] // self.TILE_SIZE)
        mouse_tile_y = int(mapped_mouse_pos[1] // self.TILE_SIZE)

        print(f"Turret placement attempt at tile ({mouse_tile_x}, {mouse_tile_y})")

        # Center the turret within the tile
        pixel_x = mouse_tile_x * self.TILE_SIZE + self.TILE_SIZE // 2
        pixel_y = mouse_tile_y * self.TILE_SIZE + self.TILE_SIZE // 2

        # Calculate the sequential number of clicked tile
        mouse_tile_num = (mouse_tile_y * self.COLS) + mouse_tile_x

        # Check if the tile is sand (tile ID 161)
        if self.world.tile_map[mouse_tile_num] == 161:
            # Check if turret is not already placed in tile
            if self.occupied_tiles.get(mouse_tile_num) is None:
                # Choose appropriate sprite sheets based on turret type
                if self.current_turret_type == "standard":
                    sprite_sheets = self.turret_spritesheets
                elif self.current_turret_type == "camo":
                    sprite_sheets = self.camo_turret_spritesheets
                elif self.current_turret_type == "purple":
                    sprite_sheets = self.purple_turret_spritesheets
                else:
                    sprite_sheets = self.turret_spritesheets  # Default to standard

                turret = Turret(
                    sprite_sheets,
                    self.current_turret_type,
                    mouse_tile_x,
                    mouse_tile_y,
                    pixel_x,
                    pixel_y,
                )
                self.turret_group.add(turret)
                self.occupied_tiles[mouse_tile_num] = True
                self.placement_message = "Turret placed successfully!"
                self.message_timer = pygame.time.get_ticks()
                print(
                    f"Turret placed at tile ({mouse_tile_x}, {mouse_tile_y}) as {self.current_turret_type} "
                    f"turret"
                )
                return True  # Turret successfully placed
            else:
                self.placement_message = "Tile is already occupied!"
                self.message_timer = pygame.time.get_ticks()
                print(f"Tile ({mouse_tile_x}, {mouse_tile_y}) is already occupied.")
        else:
            self.placement_message = "Invalid placement area."
            self.message_timer = pygame.time.get_ticks()
            print(f"Tile ({mouse_tile_x}, {mouse_tile_y}) is not a valid placement area.")

        return False  # Placement failed

    def select_turret(self, mapped_mouse_pos):
        """
        Selects a turret at the given mouse position.

        Args:
            mapped_mouse_pos (tuple): The mapped position of the mouse click.

        Returns:
            Turret or None: The selected turret or None if no turret is found.
        """
        mouse_tile_x = int(mapped_mouse_pos[0] // self.TILE_SIZE)
        mouse_tile_y = int(mapped_mouse_pos[1] // self.TILE_SIZE)

        for turret in self.turret_group:
            if (mouse_tile_x, mouse_tile_y) == (
                turret.mouse_tile_x,
                turret.mouse_tile_y,
            ):
                print(f"Selected turret at tile ({mouse_tile_x}, {mouse_tile_y})")
                return turret

        print("No turret selected")
        return None

    def reset_occupied_tiles(self):
        """Clear all occupied tiles."""
        self.occupied_tiles.clear()

    def restart_level(self):
        """Restart game variables."""
        self.state = "menu"
        self.game_status = 0
        self.wave_started = False
        self.placing_turrets = False
        self.selected_turret = None
        self.last_enemy_spawn = pygame.time.get_ticks()
        self.current_turret_type = "standard"

        # Reset world instance
        self.world = World(self.world_data, self.map_image)
        self.world.process_data()
        self.world.process_enemies()

        # Empty groups
        self.enemy_group.empty()
        self.turret_group.empty()

        # Reset occupied tiles
        self.occupied_tiles = {}

        # Clear placement message
        self.placement_message = ""
        self.message_timer = 0

        print("Level restarted and player moved to Menu.")

    def handle_events(self):
        """
        Handle all events.

        Returns:
            bool: False if the game should exit, True otherwise.

        Behavior:
            - Processes user inputs for turret placement, map selection, and button clicks.
        """
        for event in pygame.event.get():
            # Quit program
            if event.type == pygame.QUIT:
                return False
            # Window resize
            if event.type == pygame.VIDEORESIZE:
                self.display_surface = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                print(f"Window resized to: {event.w}x{event.h}")
            # Mouse click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left Mouse Button
                mouse_pos = pygame.mouse.get_pos()
                # Map mouse position to internal screen coordinates
                mapped_mouse_pos = self.map_mouse_cursor(mouse_pos)

                if self.state == "menu":
                    # Check if any map image was clicked
                    for i in range(len(self.menu_map_rects)):
                        rect = self.menu_map_rects[i]
                        if rect.collidepoint(mapped_mouse_pos):
                            self.selected_map = i + 1  # Maps are 1, 2, 3
                            print(f"Map {self.selected_map} selected.")
                            self.load_level_data(self.selected_map)
                            # Create world instance
                            self.world = World(self.world_data, self.map_image)
                            self.world.process_data()
                            self.world.process_enemies()
                            self.state = "game"  # Transition to game
                            break
                    else:
                        # Difficulty button
                        if self.difficulty_button.draw(self.screen, mapped_mouse_pos):
                            # Change difficulty level
                            self.current_difficulty_index = (self.current_difficulty_index + 1) % len(
                                self.difficulties
                            )
                            self.selected_difficulty = self.difficulties[self.current_difficulty_index]
                            # Update button image
                            self.difficulty_button.image = self.difficulty_images[
                                self.current_difficulty_index
                            ]
                            print(f"Difficulty set to {self.selected_difficulty.capitalize()}.")

                elif self.state == "game":
                    # Check if mouse is on the game area
                    if mapped_mouse_pos[0] < self.SCREEN_WIDTH and mapped_mouse_pos[1] < self.SCREEN_HEIGHT:
                        if self.placing_turrets:
                            buy_cost = self.turret_buy_costs.get(self.current_turret_type)
                            if self.world.money >= buy_cost:
                                if self.create_turret(mapped_mouse_pos):
                                    self.world.money -= buy_cost
                                    self.placing_turrets = (
                                        False  # Exit placement mode after successful placement
                                    )
                            else:
                                self.placement_message = "Not enough money to place turret!"
                                self.message_timer = pygame.time.get_ticks()
                                print("Not enough money to place turret.")
                        else:
                            self.selected_turret = self.select_turret(mapped_mouse_pos)
                            for turret in self.turret_group:
                                turret.selected = False  # Reset flag for all turrets
                            if self.selected_turret:
                                self.selected_turret.selected = True
                                print(
                                    f"Turret selected at position ({self.selected_turret.x}, {self.selected_turret.y})"
                                )

        return True

    def update(self):
        """
        Update game logic.

        Behavior:
            - Checks for win/loss conditions.
            - Updates enemy and turret groups.
        """
        if self.state == "game":
            if self.world.health <= 0:
                self.game_status = -1  # Indicate loss
                self.state = "game_over"  # Transition to game_over state
                print("Transitioning to Game Over state.")
            elif self.world.level > self.MAX_LEVELS:
                self.game_status = 1  # Indicate win
                self.state = "game_over"  # Transition to game_over state
                print("Transitioning to Game Over state.")
            else:
                # Continue updating enemies and turrets
                self.enemy_group.update(self.world)
                self.turret_group.update(self.enemy_group)

    def skip_wave(self):
        """
        Skip the current wave by killing all enemy sprites on screen ending wave immediately

         Behavior:
            - Removes all enemies from the screen.
            - Deducts a health penalty based on enemy damage..
        """
        if not self.wave_started:
            return
        total_penalty = 0
        enemies_to_skip = list(self.enemy_group)  # create a copy of current enemy group

        for enemy in enemies_to_skip:
            # Use each enemy's damage_inflicted as the penalty for skipping it
            total_penalty += enemy.damage_inflicted
            enemy.kill()  # Remove the enemy

        self.world.health -= total_penalty
        print(
            f"Skiped wave: {len(enemies_to_skip)} enemies removed; total health penalty: {total_penalty}."
        )

        self.world.money += c.WAVE_COMPLETE_REWARD
        self.wave_started = False
        self.last_enemy_spawn = pygame.time.get_ticks()
        self.world.reset_values()
        self.world.process_enemies()
        for turret in self.turret_group:
            turret.reset_tidal_upgrade()

    def draw_menu(self):
        """Draw the map selection menu."""
        self.screen.fill("dodgerblue")
        title_text = self.large_font.render("Select Map", True, "white")
        title_rect = title_text.get_rect()
        title_rect.center = (self.SCREEN_WIDTH // 2 + 190, 280)
        self.screen.blit(title_text, title_rect)

        # Iterate through all map images
        for i in range(len(self.menu_map_images)):
            img = self.menu_map_images[i]  # Get the current map image
            rect = self.menu_map_rects[i]  # Get the corresponding position rectangle
            self.screen.blit(img, rect)

        # Drawing "Difficulty" label
        difficulty_title = self.text_font.render("DIFFICULTY:", True, "white")
        difficulty_rect = difficulty_title.get_rect()
        # Position the label above the difficulty button
        difficulty_rect.center = (self.SCREEN_WIDTH // 2 + 200, 750)
        self.screen.blit(difficulty_title, difficulty_rect)

        # Drawing the difficulty button
        self.difficulty_button.draw(self.screen, self.map_mouse_cursor(pygame.mouse.get_pos()))

    def draw_game_over(self):
        """Draw the game over screen."""
        print("GAME OVER")

        overlay = pygame.Surface(
            (self.SCREEN_WIDTH + self.SIDE_PANEL, self.SCREEN_HEIGHT),
            pygame.SRCALPHA,
        )
        self.screen.blit(overlay, (0, 0))

        # Draw a central rectangle for the Game Over message and buttons
        game_over_rect = pygame.Rect(
            (self.SCREEN_WIDTH + self.SIDE_PANEL) // 2 - 200,
            self.SCREEN_HEIGHT // 2 - 100,
            400,
            200,
        )
        pygame.draw.rect(self.screen, "dodgerblue", game_over_rect, border_radius=30)

        # Display the game over message
        if self.game_status == -1:
            message = "GAME OVER"
        elif self.game_status == 1:
            message = "YOU WIN!"
        else:
            message = "GAME OVER"  # Default message

        self.draw_text(
            message,
            self.large_font,
            "white",
            game_over_rect.centerx - 80,
            game_over_rect.centery - 50,
        )

        # Draw the Restart Button
        if self.restart_button.draw(self.screen, self.map_mouse_cursor(pygame.mouse.get_pos())):
            self.restart_level()
            print("Restart button clicked. Returning to Menu.")

    def draw_game(self):
        """
        Draw all game elements.

        Behavior:
            - Renders the game world, turrets, enemies, and side panel information."""
        # Fill the main game area with background color
        self.screen.fill(self.BACKGROUND_COLOR)

        # Fill the side panel with desired color
        side_panel_rect = pygame.Rect(self.SCREEN_WIDTH, 0, self.SIDE_PANEL, self.SCREEN_HEIGHT)
        self.screen.fill(self.SIDE_PANEL_COLOR, side_panel_rect)

        # Draw the game world (map, paths, etc.)
        self.world.draw(self.screen)

        # Draw enemies
        self.enemy_group.draw(self.screen)

        # Draw health bars for each enemy
        for enemy in self.enemy_group:
            enemy.draw_health_bar(self.screen)

        # Draw turrets
        for turret in self.turret_group:
            turret.draw(self.screen)  # Custom draw method

        # Draw side panel info
        self.draw_text(
            "health: " + str(self.world.health),
            self.text_font,
            "white",
            self.SCREEN_WIDTH + 20,
            20,
        )
        self.draw_text(
            "money: " + str(self.world.money),
            self.text_font,
            "white",
            self.SCREEN_WIDTH + 20,
            50,
        )
        self.draw_text(
            "wave: " + str(self.world.level),
            self.text_font,
            "white",
            self.SCREEN_WIDTH + 20,
            80,
        )
        # drawing prices of turrets

        self.draw_text(
            "200 $",
            self.text_font,
            "white",
            self.SCREEN_WIDTH + 45,
            120 + 80,
        )
        self.draw_text(
            "500 $",
            self.text_font,
            "white",
            self.SCREEN_WIDTH + 45 + 90,
            120 + 80,
        )
        self.draw_text(
            "200 $",
            self.text_font,
            "white",
            self.SCREEN_WIDTH + 45 + 90 + 90,
            120 + 80,
        )

        # Get and map current mouse position
        mouse_pos = pygame.mouse.get_pos()
        mapped_mouse_pos = self.map_mouse_cursor(mouse_pos)

        # Check if wave has been started
        if self.state == "game":
            if self.wave_started:
                if pygame.time.get_ticks() - self.last_enemy_spawn > c.SPAWN_COOLDOWN:
                    if self.world.spawned_enemies < len(self.world.enemy_list):
                        # Spawn enemies
                        enemy_type = self.world.enemy_list[self.world.spawned_enemies]
                        enemy = Enemy(
                            enemy_type,
                            self.world.waypoints,
                            self.enemy_images,
                            difficulty=self.selected_difficulty,
                        )
                        self.enemy_group.add(enemy)
                        self.world.spawned_enemies += 1
                        self.last_enemy_spawn = pygame.time.get_ticks()
                        print(f"Enemy spawned: {enemy_type}, Total enemies: {len(self.enemy_group)}")
            else:
                if self.begin_button.draw(self.screen, mapped_mouse_pos):  # Button clicked
                    self.wave_started = True
                    print("Wave started.")

            # pygame.draw.lines(self.screen, "grey0", False, self.world.waypoints)
            # Check if the wave is completed
            if self.world.is_wave_completed():
                if self.world.level > self.MAX_LEVELS:
                    self.game_status = 1  # Win
                    self.state = "game_over"  # Transition to game_over state
                    print("Transitioning to Game Over state.")
                else:
                    self.world.money += c.WAVE_COMPLETE_REWARD
                    self.wave_started = False
                    self.last_enemy_spawn = pygame.time.get_ticks()
                    self.world.reset_values()
                    self.world.process_enemies()
                    for turret in self.turret_group:
                        turret.reset_tidal_upgrade()

                    print(f"Wave completed! Level increased to {self.world.level}")

            # Draw Turret Buttons
            if self.turret_button.draw(self.screen, mapped_mouse_pos):  # Returns True if clicked
                self.placing_turrets = True
                self.current_turret_type = "standard"
                self.placement_message = "Placing Standard Turret"
                self.message_timer = pygame.time.get_ticks()  # Resetting timer
                print("Standard Turret placement mode enabled.")

            if self.camo_turret_button.draw(self.screen, mapped_mouse_pos):
                self.placing_turrets = True
                self.current_turret_type = "camo"
                self.placement_message = "Placing Camo Turret"
                self.message_timer = pygame.time.get_ticks()
                print("Camo Turret placement mode enabled.")

            if self.purple_turret_button.draw(self.screen, mapped_mouse_pos):
                self.placing_turrets = True
                self.current_turret_type = "purple"
                self.placement_message = "Placing Purple Turret"
                self.message_timer = pygame.time.get_ticks()
                print("Purple Turret placement mode enabled.")

            # Check if the turret placement mode is active
            if self.placing_turrets:
                # Use mapped_mouse_pos for internal screen
                cursor_pos = mapped_mouse_pos

                # Assign the appropriate cursor image based on the current turret type
                if self.current_turret_type == "standard":
                    current_cursor = self.cursor_standard  # Standard cursor
                elif self.current_turret_type == "camo":
                    current_cursor = self.cursor_camo_turret  # Camo cursor
                elif self.current_turret_type == "purple":
                    current_cursor = self.cursor_purple_turret  # Purple cursor
                else:
                    current_cursor = self.cursor_standard  # Default to standard

                cursor_rect = current_cursor.get_rect()
                cursor_rect.midtop = cursor_pos  # Align the bottom center of the cursor image with cursor_pos

                # print(f"[DEBUG] Cursor Position: {cursor_pos}, Turret Rect: {cursor_rect}")

                # Only display the turret cursor within the game screen area
                if cursor_pos[0] <= self.SCREEN_WIDTH and cursor_pos[1] <= self.SCREEN_HEIGHT:
                    self.screen.blit(current_cursor, cursor_rect)  # Use the selected cursor image

                # Draw and handle the cancel button
                if self.cancel_button.draw(self.screen, mapped_mouse_pos):
                    self.placing_turrets = False
                    self.placement_message = "Turret placement canceled."
                    self.message_timer = pygame.time.get_ticks()
                    print("Turret placement mode disabled.")

            # IF turret is selected
            if self.selected_turret:
                # Draw UPGRADE button for standard upgrade
                if self.selected_turret.turret_level < len(TURRET_DATA[self.selected_turret.turret_type]):
                    if self.upgrade_button.draw(self.screen, mapped_mouse_pos):
                        if not self.selected_turret.tidal_active:
                            if self.world.money >= c.UPGRADE_COST:
                                self.world.money -= c.UPGRADE_COST
                                self.selected_turret.upgrade()
                                print(
                                    f"Turret at ({self.selected_turret.x}, {self.selected_turret.y}) upgraded "
                                    f"to level {self.selected_turret.turret_level}"
                                )
                                self.placement_message = "Turret upgraded successfully!"
                                self.message_timer = pygame.time.get_ticks()
                            else:
                                self.placement_message = "Not enough money to upgrade turret!"
                                self.message_timer = pygame.time.get_ticks()
                                print("Not enough money to upgrade turret!")
                        else:
                            self.placement_message = "You can't upgrade turret, while it's tidally upgraded"
                            self.message_timer = pygame.time.get_ticks()
                            print("You can't upgrade turret, while it's tidally upgraded")

                if self.tidal_upgrade_button.draw(self.screen, mapped_mouse_pos):
                    if self.wave_started:
                        if self.selected_turret:
                            # Check if the turret is eligible for a tidal upgrade
                            if not self.selected_turret.tidal_used and not self.selected_turret.tidal_active:
                                if self.world.money >= c.TIDAL_UPGRADE_COST:
                                    self.world.money -= c.TIDAL_UPGRADE_COST
                                    self.selected_turret.tidally_upgrade()
                                    print(
                                        f"Turret at ({self.selected_turret.x}, {self.selected_turret.y}) "
                                        f"has been tidally upgraded"
                                    )
                                else:
                                    self.placement_message = "Not enough money for tidal upgrade!"
                                    self.message_timer = pygame.time.get_ticks()
                                    print("Not enough money for tidal upgrade.")
                            else:
                                print("Turret cannot receive tidal upgrade again this round.")
                    else:
                        self.placement_message = "Start new round to tidally upgrade turret"
                        self.message_timer = pygame.time.get_ticks()
                        print("Start new round to tidally upgrade turret")

                # Draw SELL button
                if self.sell_button.draw(self.screen, mapped_mouse_pos):
                    turret_type = self.selected_turret.turret_type
                    sell_price = (
                        self.turret_buy_costs.get(turret_type) * c.SELL_RETURN_RATE
                    )  # 30% of original cost of the turret
                    self.world.money += int(sell_price)
                    print(
                        f"Sold turret at ({self.selected_turret.x}, {self.selected_turret.y}) for {int(sell_price)} $"
                    )

                    # Remove turret from group
                    self.turret_group.remove(self.selected_turret)

                    # Mark tile as unoccupied
                    turret_tile_num = (
                        self.selected_turret.mouse_tile_y * self.COLS
                    ) + self.selected_turret.mouse_tile_x

                    if turret_tile_num in self.occupied_tiles:
                        del self.occupied_tiles[turret_tile_num]

                    # Reset selected turret
                    self.selected_turret = None

                    # Add placement message
                    self.placement_message = "Turret sold successfully!"
                    self.message_timer = pygame.time.get_ticks()

            # Draw return to menu button
            if self.back_to_menu_button.draw(self.screen, mapped_mouse_pos):
                self.restart_level()
                print("Back to Menu button clicked. Returning to Menu.")

            # Draw the skip button and its penalty text
            if self.world.spawned_enemies == len(self.world.enemy_list) and len(self.enemy_group) > 0:
                if self.skip_button.draw(self.screen, mapped_mouse_pos):
                    self.skip_wave()
                # Calculate total penalty that would be applied if skip is used
                total_penalty = sum(enemy.damage_inflicted for enemy in self.enemy_group)
                penalty_text = f"Skip Penalty: -{total_penalty} health"
                # Draw the penalty text below the skip button.
                self.draw_text(
                    penalty_text,
                    self.small_text_font,
                    "red",
                    self.SCREEN_WIDTH + 30,
                    self.skip_button.rect.bottom + 10,
                )

            # Display placement message if any exist
            if self.placement_message:
                current_time = pygame.time.get_ticks()
                if current_time - self.message_timer < 2000:  # Display message for 2 seconds
                    if "successfully" in self.placement_message:
                        color = "green"
                    else:
                        color = "red"
                    self.draw_text(
                        self.placement_message,
                        self.text_font,
                        color,
                        self.SCREEN_WIDTH + 20,
                        self.SCREEN_HEIGHT - 30,
                    )
                else:
                    self.placement_message = ""  # Clear message after 2 seconds

    def draw(self):
        """Draw the appropriate screen based on the current state."""
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "game":
            self.draw_game()
        elif self.state == "game_over":
            self.draw_game_over()

        # Scale self.screen to fit display_surface
        scaled_screen = pygame.transform.scale(self.screen, self.display_surface.get_size())
        self.display_surface.blit(scaled_screen, (0, 0))

        pygame.display.update()

    def run(self):
        """
        Runs the main game loop.

        Behavior:
            - Handles events, updates game logic, and renders the screen.
        """
        run = True
        while run:
            self.clock.tick(self.FPS)
            run = self.handle_events()
            self.update()
            self.draw()
        pygame.quit()

    def map_mouse_cursor(self, pos):
        """
        Map the mouse position from display_surface to internal screen coordinates.

         Args:
            pos (tuple): The raw mouse position.

        Returns:
            tuple: The mapped mouse position on the internal screen.

        Behavior:
         - Determines the scaling factor for both x and y directions based on the ratio of
          the internal game screen's dimensions to the display surface's dimensions.
         - Multiplies the raw mouse coordinates by the scaling factors to map them to
          internal screen coordinates.

        """
        display_width, display_height = self.display_surface.get_size()  # Get current window size
        screen_width, screen_height = self.screen.get_size()  # Get internal game screen size

        # Calculate scaling factors for x and y axes
        scale_x = screen_width / display_width
        scale_y = screen_height / display_height

        # Scale raw mouse position to internal screen coordinates
        mapped_x = pos[0] * scale_x
        mapped_y = pos[1] * scale_y

        # print(f"Original mouse pos: {pos} -> Mapped mouse pos: ({mapped_x}, {mapped_y})")
        return mapped_x, mapped_y


if __name__ == "__main__":
    game = Game()
    game.run()
