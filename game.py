import pygame
import sys
import time

from scripts.utility import load_image, load_images, Animation, save_to_excel, get_user_input
from scripts.entities import Player
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds

RES_WIDTH = 1920
RES_HEIGHT = 1080


# Klasa do Tworzenia przycisków
class Button:
    def __init__(self, text, x, y, width, height, color=(255, 255, 255)):
        # Atrybutyd
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.font = pygame.font.Font(None, 50)

    # Metoda do rysowania przycisków
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    # Metoda sprawdzająca, czy kursor myszy jest na przycisku
    def is_clicked(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())


# Główna klasa gry
class Game:
    def __init__(self):
        pygame.init()
        # Podstawowe atrybuty dotyczące rozmiaru i tytułu okna, wraz z ograniczeniem fps
        pygame.display.set_caption("Platform Jumper")
        self.screen = pygame.display.set_mode((RES_WIDTH, RES_HEIGHT))
        self.display = pygame.Surface((RES_WIDTH/2, RES_HEIGHT/2))
        self.clock = pygame.time.Clock()
        # Atrybuty dotyczące movementu i startowa pozycja gracza
        self.movement = [False, False]
        self.player_startpos = (1, 200)
        # Słownik z teksturami używający funkcji "load_images" z pliku utility do załadowania png
        self.assets = {
            "grass": load_images("tiles/grass"),
            "stone": load_images("tiles/stone"),
            "Evil-Purple": load_images("tiles/Evil-Purple"),
            "Pyramid-Yellow": load_images("tiles/Pyramid-Yellow"),
            "Castle-blue": load_images("tiles/Castle-blue"),
            "Diamond-Blue": load_images("tiles/Diamond-Blue"),
            "Emerald-Green": load_images("tiles/Emerald-Green"),
            "grass_purple": load_images("tiles/grass_purple"),
            "grass_thick_snow": load_images("tiles/grass_thick_snow"),
            "plain_snow": load_images("tiles/plain_snow"),
            "ice": load_images("tiles/ice"),
            "win_tiles": load_images("tiles/win_tiles"),
            "Winter Wilds": load_image("WWilds.png"),
            # TODO: CHANGE TO GTOWER.png
            "Galactic Tower": load_image("black.png"),
            "Corrupted Fields": load_image("CFields.png"),
            "clouds": load_images("clouds"),
            "player": load_image("player_correct.png"),
            # TODO: CHANGE TO 10,10,4,4
            "player/idle": Animation(load_images("entities/player/idle"), img_dur=99999999999999999999999999999999999999),
            "player/run": Animation(load_images("entities/player/run"), img_dur=99999999999999999999999999999999999999),
            "player/jump": Animation(load_images("entities/player/jump"), img_dur=99999999999999999999999999999999999999),
            "player/fall": Animation(load_images("entities/player/fall")),
            "player/crouch": Animation(load_images("entities/player/crouch"), img_dur=99999999999999999999999999999999999999),
        }
        # Stworzenie chmur z użyciem klasy z pliku clouds
        self.clouds = Clouds(self.assets["clouds"], count=16)
        # Stworzenie "gracza" używając klasy z pliku entities, podając pozycję startową i wielkość postaci
        self.player = Player(self, self.player_startpos, (16, 28))
        # Stworzenie mapy klocków używając klasy z pliku tilemap
        self.tilemap = Tilemap(self, tile_size=16)
        # Atrybut scroll do poruszania się kamery za graczem
        self.scroll = [0, 0]
        # Atrybut z czasem rozpoczęcia gry to późniejszego liczenia go i wyświetlania
        self.start_time = 0
        # Załadowanie tła menu i przeskalowanie go
        # TODO: CHANGE TO MENU_BG.png
        self.background_menu = pygame.image.load("data/images/black.png")
        self.background_menu = pygame.transform.scale(self.background_menu, (RES_WIDTH, RES_HEIGHT))
        # Atrybut z obecnym poziomem
        self.current_level = None

    # Metoda do resetowania atrybutów przed kolejnym rozpoczęciem rozgrywki
    def reset(self):
        self.movement = [False, False]
        # Win pos
        # self.player_startpos = (100, -1700)
        self.player_startpos = (1, 200)
        self.player = Player(self, self.player_startpos, (16, 28))
        self.scroll = [0, 0]
        self.start_time = pygame.time.get_ticks()
        self.current_level = None
        self.player.win = False
        self.player.total_jumps = 0

    # Metoda tworząca i wyświetlająca main menu
    def main_menu(self):
        # Stworzenie przycisków "Play" i "Exit" używając klasy Button
        play_button = Button('Play', RES_WIDTH/2-100, RES_HEIGHT/2-50, 200, 50)
        exit_button = Button('Exit', RES_WIDTH/2-100, RES_HEIGHT/2+10, 200, 50)
        # Głowna pętla menu czekająca na eventy od gracza
        while True:
            self.reset()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Wykorzystanie metody z klasy button (.is_clicked), by wiedzieć, czy kursor jest nad guzikiem
                    if play_button.is_clicked():
                        self.level_picker()
                    elif exit_button.is_clicked():
                        pygame.quit()
                        sys.exit()
            # Wyświetlenie
            self.screen.blit(self.background_menu, (0, 0))
            play_button.draw(self.screen)
            exit_button.draw(self.screen)
            pygame.display.update()
            self.clock.tick(60)

    # Metoda do stworzenia i wyświetlenia menu z level_picker'em
    def level_picker(self):
        # Tablica wszystkich poziomów
        # TODO: UNCOMMENT
        #levels = ['Galactic Tower', 'Winter Wilds', 'Corrupted Fields']
        levels = ['Galactic Tower']
        # Stworzenie przycisków
        buttons = [Button(level, RES_WIDTH/2-150, RES_HEIGHT/2-50 + i * 60, 300, 50) for i, level in enumerate(levels)]
        # Główna pętla level_picker'a
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, button in enumerate(buttons):
                        if button.is_clicked():
                            self.current_level = str(levels[i])
                            self.run(levels[i])
            # Wyświetlenie
            self.screen.blit(self.background_menu, (0, 0))
            for button in buttons:
                button.draw(self.screen)
            pygame.display.update()
            self.clock.tick(60)

    # Metoda do wyświetlenia podsumowania po przejściu poziomu
    def display_summary(self, ending_time):
        # Przezroczyste czarne tło
        background = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        background.set_alpha(200)
        background.fill((0, 0, 0))
        self.screen.blit(background, (0, 0))

        # Czcionka i rozmiar
        font = pygame.font.Font("data/fonts/font.ttf", 64)
        font_end = pygame.font.Font(None, 32)

        # Utwórz tekst "You Win"
        win_text = font.render("You Win", True, (255, 255, 255))

        # Utwórz tekst dla czasu, total_jumps, username
        time_text = font.render("Time: " + ending_time, True, (255, 255, 255))
        jumps_text = font.render("Jumps: " + str(self.player.total_jumps), True, (255, 255, 255))
        username_text = font.render("Enter your name", True, (255, 255, 255))

        # Wyświetl tekst na ekranie
        self.screen.blit(win_text, ((self.screen.get_width() / 2) - 164, (self.screen.get_height() / 4.5) - 50))
        self.screen.blit(time_text, ((self.screen.get_width() / 2) - 464, self.screen.get_height() / 3.5 + 50))
        self.screen.blit(jumps_text, ((self.screen.get_width() / 2) + 100, self.screen.get_height() / 3.5 + 50))
        self.screen.blit(username_text, ((self.screen.get_width() / 2) - 400, self.screen.get_height() / 3.5 + 200))
        end1_text = font_end.render("Press enter to confirm, then", True, (255, 255, 255))
        end2_text = font_end.render("Press space to leave to main menu", True, (255, 255, 255))
        self.screen.blit(end1_text, ((self.screen.get_width() / 2) - 150, self.screen.get_height() / 3.5 + 420))
        self.screen.blit(end2_text, ((self.screen.get_width() / 2) - 190, self.screen.get_height() / 3.5 + 470))

        # Pobierz username
        user_name = get_user_input(self.screen)

        # Zapisywanie do xlsx używając funkcji z pliku utility
        save_to_excel(user_name, ending_time, self.player.total_jumps, self.current_level)

        # Pętla czekająca na naciśnięcie spacji
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    # Jeśli naciśnięto spację, wyjdź z pętli
                    if event.key == pygame.K_SPACE:
                        self.main_menu()
            # Aktualizuj ekran
            pygame.display.update()
            # Czekaj krótką chwilę przed następnym sprawdzeniem
            pygame.time.wait(100)

    # Metoda do uruchomienia gry
    def run(self, level=None):
        # Sprawdza jaki level załadować
        if level is not None:
            self.tilemap.load("data/map/" + str(level) + ".json")
            self.start_time = pygame.time.get_ticks()

        # Główna pętla gry
        while True:
            # Sprawdzenie, czy gracz wygrał
            if self.player.win:
                # TODO: UNCOMMENT AND DELETE EXIT(0)
                #self.display_summary(time_str)
                exit(0)
                elapsed_time = 0
                pygame.display.update()
            else:
                # Tlo dynamiczne
                #self.display.blit(self.assets[self.current_level], (0, 0))
                self.display.blit(pygame.transform.scale(self.assets[self.current_level], (self.display.get_width(), self.display.get_height())), (0, 0))
                # Przesuwanie "kamery" za graczem
                self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
                self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
                render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

                # Chmury
                if level == "Winter Wilds" or level == "Corrupted Fields":
                    self.clouds.update()
                    self.clouds.render(self.display, offset=render_scroll)

                # Klocki
                self.tilemap.render(self.display, offset=render_scroll)

                # Update gracza (pozycja, animacja itd.)
                # True = 1 False = 0 dzięki temu można kontrolować ruch (czy w prawo, czy w lewo)
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))

                # Render gracza
                self.player.render(self.display, offset=render_scroll)

                self.tilemap.render_offset(self.display, offset=render_scroll)


                # Timer
                elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000
                minutes = int(elapsed_time / 60)
                seconds = int(elapsed_time % 60)
                time_str = f"{minutes:02}:{seconds:02}"
                time_font = pygame.font.Font(None, 60)
                time_text = time_font.render(time_str, True, (255, 255, 255))

                # TODO: UNCOMMENT
                # if self.player.jumping:
                #     jump_duration = time.time() - self.player.jump_start_time
                #     self.player.jump_power = min(jump_duration, self.player.max_jump_power)

                # # Rysowanie paska siły skoku
                # if self.player.jumping:
                #     filled_width = int(100 * (self.player.jump_power / self.player.max_jump_power))
                #     bar_height = 5
                #     bar_x = self.player.rect().centerx - render_scroll[0] - 50  # Adjust for camera scroll
                #     bar_y = self.player.rect().top - render_scroll[1] - 20  # Adjust for camera scroll
                #
                #     # Draw the filled portion of the bar (orange)
                #     pygame.draw.rect(self.display, (255, 165, 0), (bar_x, bar_y, filled_width, bar_height))
                #     # Draw the remaining portion of the bar (gray)
                #     pygame.draw.rect(self.display, (128, 128, 128),
                #                      (bar_x + filled_width, bar_y, 100 - filled_width, bar_height))
                    # Draw the border of the bar (black) optionally
                    #pygame.draw.rect(self.display, (0, 0, 0), (bar_x, bar_y, 100, bar_height), 2)

                # Event handler
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        self.player.last_movement = 2
                        # Jeśli w to skok
                        if event.key == pygame.K_w:
                            self.player.jumping = True
                            jump_start = time.time()
                            self.player.jump_start_time = time.time()
                            self.movement = [0, 0]
                            self.player.jump_time = time.time()
                        # Only allow left/right movement if not jumping
                        if not self.player.jumping:
                            if event.key == pygame.K_a:
                                self.movement[0] = True
                            if event.key == pygame.K_d:
                                self.movement[1] = True
                        else:
                            if event.key == pygame.K_a:
                                self.player.last_movement = 1
                            if event.key == pygame.K_d:
                                self.player.last_movement = 0

                    if event.type == pygame.KEYUP:
                        if event.key == pygame.K_a:
                            self.movement[0] = False
                        if event.key == pygame.K_d:
                            self.movement[1] = False
                        if event.key == pygame.K_w:
                            self.player.jumping = False
                            jump_duration = time.time() - self.player.jump_start_time
                            self.player.jump_power = min(jump_duration, self.player.max_jump_power)
                            self.player.jump(self.player.jump_power)
                            self.player.reset_jump_power()
                # Wyświetlenie wszystkiego na ekran
                self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

                # TODO: UNCOMMENT
                #self.screen.blit(time_text, (10, 10))
                pygame.display.update()
                self.clock.tick(60)  # ograniczenie do 60fps


if __name__ == "__main__":
    Game().main_menu()
