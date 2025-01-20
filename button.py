import pygame


class Button:
    def __init__(self, x, y, image, single_click):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False
        self.single_click = single_click

    def draw(self, surface, mouse_pos):
        """
        Draw the button on the given surface and check for click events.

        :param surface: Pygame surface to draw the button on.
        :param mouse_pos: Tuple of (x, y) coordinates of the mouse position, already mapped to the game surface.
        :return: True if the button was clicked, False otherwise.
        """
        action = False

        if self.rect.collidepoint(mouse_pos):  # Check if the mouse cursor is over the buttons rectangle
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                action = True

                if self.single_click:
                    # we want to make sure that if statement is not executing again
                    # to prevent repeated triggering with one click
                    self.clicked = True

        # If the mouse button is released we reset the clicked flag back to False
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        # draw button on screen
        surface.blit(self.image, self.rect)

        return action
