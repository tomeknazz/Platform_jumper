import sys
import time

import pygame

from scripts.audio import Audio
from scripts.clouds import Clouds
from scripts.entities import Player
from scripts.tilemap import Tilemap
from scripts.utility import load_image, load_images, Animation, save_to_excel, load_from_excel

RES_WIDTH = 1920
RES_HEIGHT = 1080


# Klasa do Tworzenia przycisków
class Button:
    def __init__(self, text, x, y, width, height, image_path, offset_x=0, offset_y=0,
                 font_path="data/fonts/font1.ttf", font_size=50,
                 flip_x=False, flip_y=False, highlight=True):

        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.offset = (offset_x, offset_y)

        # Załaduj i ewentualnie odwróć obraz
        original_image = pygame.image.load(image_path).convert_alpha()
        if flip_x or flip_y:
            original_image = pygame.transform.flip(original_image, flip_x, flip_y)

        self.original_image = original_image
        self.image = self._scale_image_pixel_art(self.original_image, width, height)
        self.highlight = highlight
        self.font = pygame.font.Font(font_path, font_size)
        self.hover_image = self._create_hover_image(self.image)

    def _create_hover_image(self, image):
        hover = image.copy()
        # Bez pętli piksel po pikselu – szybciej przez powierzchnię
        brightness_surface = pygame.Surface(image.get_size()).convert_alpha()
        brightness_surface.fill((20, 20, 0, 0))  # tylko podbij RGB
        hover.blit(brightness_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        return hover

    @staticmethod
    def _scale_image_pixel_art(image, target_w, target_h):
        img_w, img_h = image.get_size()
        scale_x = target_w // img_w
        scale_y = target_h // img_h
        scale = min(scale_x, scale_y)

        new_size = (img_w * scale, img_h * scale)
        return pygame.transform.scale(image, new_size)

    def draw(self, screen, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        image_rect = self.image.get_rect(center=self.rect.center)
        image_rect.x += self.offset[0]
        image_rect.y += self.offset[1]

        if self.rect.collidepoint(mouse_pos) and self.highlight:
            screen.blit(self.hover_image, image_rect)
        else:
            screen.blit(self.image, image_rect)

        text_surface = self.font.render(self.text, True, (150, 40, 20))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(mouse_pos)

    @staticmethod
    def get_scaled_mouse_pos(self, screen, display):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        scale_x = display.get_width() / screen.get_width()
        scale_y = display.get_height() / screen.get_height()
        return int(mouse_x * scale_x), int(mouse_y * scale_y)


def clean_transparent_pixels(surface, replace_with=(0, 0, 0, 0)):
    width, height = surface.get_size()
    for x in range(width):
        for y in range(height):
            r, g, b, a = surface.get_at((x, y))
            if a == 0:
                # Ustaw przezroczyste piksele na neutralny kolor (np. brąz z alhpa 0)
                surface.set_at((x, y), replace_with)
    return surface


# Główna klasa gry
class Game:
    def __init__(self):
        pygame.init()
        # Podstawowe atrybuty dotyczące rozmiaru i tytułu okna, wraz z ograniczeniem fps
        pygame.display.set_caption("Platform Jumper")
        # window icon
        pygame.display.set_icon(pygame.image.load("data/images/g_icon.png"))
        # taskbar icon
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode((RES_WIDTH, RES_HEIGHT))
        self.display = pygame.Surface((RES_WIDTH / 2, RES_HEIGHT / 2))
        self.cursor_image = pygame.image.load("data/images/cursor1.png").convert_alpha()
        self.cursor_offset = (30, 32)
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
            "Galactic Tower": load_image("GTower.jpg"),
            "Corrupted Fields": load_image("CFields.png"),
            "clouds": load_images("clouds"),
            "player": load_image("player_correct.png"),
            "player/idle": Animation(load_images("entities/player/idle"), img_dur=10),
            "player/run": Animation(load_images("entities/player/run"), img_dur=10),
            "player/jump": Animation(load_images("entities/player/jump"), img_dur=4),
            "player/fall": Animation(load_images("entities/player/fall")),
            "player/crouch": Animation(load_images("entities/player/crouch"), img_dur=4),
            "bar_jumping": load_image("bar_jumping.png"),
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
        self.background_menu_original = pygame.image.load("data/images/menu_bg2.jpg").convert()
        self.background_menu = self._scale_pixel_art_image(self.background_menu_original, RES_WIDTH, RES_HEIGHT)
        # Atrybut z obecnym poziomem
        self.current_level = None
        # Add audio instance
        self.audio = Audio(self)
        # zmienne pomocnicze do setting i help
        self.settings = False
        self.help = False
        # Stworzenie przycisków
        self.help_button = Button('', RES_WIDTH * 0.01, RES_HEIGHT * 0.85, 100, 125, "data/images/help.png")
        self.settings_button = Button('', RES_WIDTH * 0.93, RES_HEIGHT * 0.01, 125, 125, "data/images/settings.png")
        self.help_text = Button('Tutaj będzie Help', RES_WIDTH / 2 - 450, RES_HEIGHT / 2 - 125 + 10, 1000, 250,
                                "data/images/banner_scroll_wide_thin.png", highlight=False)
        self.settings_text = Button('Tutaj będzie Settings', RES_WIDTH / 2 - 450, RES_HEIGHT / 2 - 125 + 10, 1000, 250,
                                    "data/images/banner_scroll_wide_thin.png", highlight=False)

    # Metoda do resetowania atrybutów przed kolejnym rozpoczęciem rozgrywki
    def reset(self):
        self.movement = [False, False]
        # Win pos
        #self.player_startpos = (100, -1700)
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
        authors_button = Button('Tomasz Nazar', RES_WIDTH * 0.75, RES_HEIGHT * 0.7 - 20, 350, 300,
                                "data/images/banner_left.png", font_size=19, highlight=False, offset_x=25, offset_y=20)
        author_1 = Button('Filip Pietrzak', RES_WIDTH * 0.75 + 10, RES_HEIGHT * 0.7 + 25, 350, 300,
                          "data/images/transparent.png", font_size=17, highlight=False, offset_x=25, offset_y=20)
        pole = Button('', RES_WIDTH * 0.75, RES_HEIGHT * 0.8 - 50, 400, 300, "data/images/pole.png", font_size=18,
                      offset_y=20, highlight=False)
        title_button = Button('Platform Jumper', RES_WIDTH / 2 - 470, RES_HEIGHT / 2 - 400, 940, 350,
                              "data/images/banner_title.png", font_size=45, offset_y=-10, highlight=False)
        play_button = Button('Play', RES_WIDTH / 2 - 180, RES_HEIGHT / 2 - 60, 360, 150,
                             "data/images/banner_scroll_wide.png")
        exit_button = Button('Exit', RES_WIDTH / 2 - 180, RES_HEIGHT / 2 + 90, 360, 150,
                             "data/images/banner_scroll_wide.png")

        # Play menu music once at menu entry
        self.audio.play_music('data/audio/menu_music.mp3', volume=0.20)
        # Głowna pętla menu czekająca na eventy od gracza
        while True:
            self.reset()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Wykorzystanie metody z klasy button (.is_clicked), by wiedzieć, czy kursor jest nad guzikiem
                    self.audio.play_sound("data/audio/click.wav")
                    if not (self.settings_button.is_clicked() or self.help_button.is_clicked()):
                        self.help = False
                        self.settings = False
                    if play_button.is_clicked():
                        pygame.mixer.stop()
                        self.audio.play_sound("data/audio/selected_button.wav")
                        self.level_picker()
                    elif exit_button.is_clicked():
                        pygame.quit()
                        sys.exit()
                    if self.help_button.is_clicked():
                        if self.settings:
                            self.settings = False
                        self.help = not self.help
                    if self.settings_button.is_clicked():
                        if self.help:
                            self.help = False
                        self.settings = not self.settings
            # Wyświetlenie

            self.screen.blit(self.background_menu, (0, 0))
            pole.draw(self.screen)
            authors_button.draw(self.screen)
            author_1.draw(self.screen)
            if not (self.settings or self.help):
                title_button.draw(self.screen)
                play_button.draw(self.screen)
                exit_button.draw(self.screen)
            if self.help:
                self.help_text.draw(self.screen)
            if self.settings:
                self.settings_text.draw(self.screen)
            # self.help_button.draw(self.screen)
            # self.settings_button.draw(self.screen)
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.screen.blit(self.cursor_image, (mouse_x - self.cursor_offset[0], mouse_y - self.cursor_offset[1]))
            pygame.display.update()
            self.clock.tick(60)

    # Metoda do stworzenia i wyświetlenia menu z level_picker'em
    def level_picker(self):
        # Tablica wszystkich poziomów
        levels = ['Galactic Tower', 'Winter Wilds', 'Corrupted Fields']

        # Stworzenie przycisków
        # return_button = Button('', RES_WIDTH/2-180, RES_HEIGHT/2+400, 360, 150, "data/images/banner_left.png")
        arrow = Button('', RES_WIDTH * 0.01, RES_HEIGHT * 0.02, 125, 125, "data/images/arrow.png", flip_x=True)
        select_level_button = Button('Select Level', RES_WIDTH / 2 - 470, RES_HEIGHT / 2 - 400, 940, 350,
                                     "data/images/banner_title.png", font_size=45, offset_y=-10, highlight=False)
        buttons = [Button(level, RES_WIDTH / 2 - 265, RES_HEIGHT / 2 - 50 + i * 120, 530, 110,
                          "data/images/banner_scroll_wide_thin.png", 0, 0, font_size=25) for i, level in
                   enumerate(levels)]
        # Główna pętla level_picker'a
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.audio.play_sound("data/audio/click.wav")
                    if not (self.settings_button.is_clicked() or self.help_button.is_clicked()):
                        self.help = False
                        self.settings = False
                    if arrow.is_clicked():
                        # Jeśli naciśnięto strzałkę, wróć do menu głównego
                        self.main_menu()
                    if self.help_button.is_clicked():
                        if self.settings:
                            self.settings = False
                        self.help = not self.help
                    if self.settings_button.is_clicked():
                        if self.help:
                            self.help = False
                        self.settings = not self.settings

                    for i, button in enumerate(buttons):
                        if button.is_clicked():
                            pygame.mixer.stop()
                            self.audio.play_sound("data/audio/selected_button.wav")
                            self.current_level = str(levels[i])
                            self.run(levels[i])
            # Wyświetlenie
            self.screen.blit(self.background_menu, (0, 0))

            # return_button.draw(self.screen)
            arrow.draw(self.screen)
            if not (self.settings or self.help):
                select_level_button.draw(self.screen)
                for button in buttons:
                    button.draw(self.screen)

            if self.help:
                self.help_text.draw(self.screen)
            if self.settings:
                self.settings_text.draw(self.screen)
            #self.help_button.draw(self.screen)
            #self.settings_button.draw(self.screen)

            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.screen.blit(self.cursor_image, (mouse_x - self.cursor_offset[0], mouse_y - self.cursor_offset[1]))
            pygame.display.update()
            self.clock.tick(60)

    # Metoda do wyświetlenia podsumowania po przejściu poziomu
    #TODO: DO NAPRAWY, DZIAŁA ALE WYGLĄDA BRZYDKO
    def display_summary(self, ending_time):
        font_32 = pygame.font.Font("data/fonts/font1.ttf", 32)
        font_24 = pygame.font.Font("data/fonts/font1.ttf", 24)
        font_20 = pygame.font.Font("data/fonts/font1.ttf", 20)
        font_16 = pygame.font.Font("data/fonts/font1.ttf", 16)
        font_10 = pygame.font.Font("data/fonts/font1.ttf", 10)


        input_active = True
        clock = pygame.time.Clock()

        input_box = pygame.Rect((self.screen.get_width() *0.4), (self.screen.get_height()  * 0.3 + 270), 400, 64)
        textcolor = pygame.Color(150, 40, 20)
        text = ''
        user_name = ''
        cursor_img = pygame.image.load("data/images/cursor1.png").convert_alpha()

        while input_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print(":)")
                        #TODO: TOMEGG JAKBYS TU DODAŁ PRZYCISKI TO SUPER, PÓŹNIEJ WYTŁUMACZE
                    elif event.key == pygame.K_RETURN:
                        user_name = text.strip()
                        if user_name != "":
                            input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        if len(text) < 19:
                            text += event.unicode

            # Rysowanie tła
            background = pygame.transform.scale(self.assets[self.current_level], (self.screen.get_width(), self.screen.get_height()))
            self.screen.blit(background, (0, 0))

            # Teksty
            self.win_banner = Button('You won!', RES_WIDTH / 2 - RES_WIDTH*0.225, RES_HEIGHT / 2 - RES_HEIGHT*0.45, RES_WIDTH*0.45, RES_HEIGHT*0.3,
                              "data/images/banner_title.png", font_size=55, offset_y=-10, highlight=False)
            self.win_banner2 = Button(
                                         '',
                                         RES_WIDTH * 0.01,
                                         RES_HEIGHT * 0.18,
                                         RES_WIDTH * 0.98,
                                         RES_HEIGHT * 0.8,
                                         "data/images/banner_big_hanging2.png",
                                         font_size=55,
                                         offset_y=-10,
                                         highlight=False
                                     )
            self.win_banner2.draw(self.screen)
            self.win_banner.draw(self.screen)
            time_text = font_32.render("Time: " + ending_time, True, textcolor)
            jumps_text = font_32.render("Jumps: " + str(self.player.total_jumps), True, textcolor)
            username_text = font_24.render("Enter your name", True, textcolor)
            end1_text = font_10.render("Press enter to confirm, then", True, textcolor)
            end2_text = font_10.render("Press space to leave to main menu", True, textcolor)
            leaderboard_text = font_16.render("Leaderboard", True, textcolor)

            self.screen.blit(time_text, ((self.screen.get_width() * 0.41), self.screen.get_height() * 0.3 + 50))
            self.screen.blit(jumps_text, ((self.screen.get_width() * 0.41), self.screen.get_height()  * 0.3 + 100))
            self.screen.blit(username_text, ((self.screen.get_width() *0.405), self.screen.get_height()  * 0.3 + 200))
            self.screen.blit(end1_text, ((self.screen.get_width() *0.425), self.screen.get_height()  * 0.3 + 350))
            self.screen.blit(end2_text, ((self.screen.get_width() *0.415), self.screen.get_height()  * 0.3 + 365))
            self.screen.blit(leaderboard_text, ((self.screen.get_width() *0.45), self.screen.get_height()  * 0.3 + 400))

            best_players = 0
            players = load_from_excel(self.current_level)
            while best_players < 3 and best_players < len(players):
                print(best_players+1,". ",players[best_players])
                player_str = f"{best_players + 1}. {players[best_players]}"
                players_text = font_10.render(player_str, True, textcolor)
                self.screen.blit(players_text,((self.screen.get_width() * 0.42), self.screen.get_height() * 0.3 + 430 + best_players * 30))
                best_players += 1

            # Input box
            txt_surface = font_20.render(text, True, textcolor)
            width = max(400, txt_surface.get_width() + 10)
            input_box.w = width
            self.inputbox = Button('', RES_WIDTH*0.375, RES_HEIGHT * 0.3,
                                     RES_WIDTH * 0.25, RES_HEIGHT * 0.32 +250,
                                     "data/images/bar_jumping.png", font_size=55, offset_y=-10, highlight=False)
            self.inputbox.draw(self.screen)
            self.screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5 ))

            #pygame.draw.rect(self.screen, color, input_box, 2) # OBRAMÓWKA DLA INPUTU

            # Kursor
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.screen.blit(cursor_img, (mouse_x - 30, mouse_y - 32))

            pygame.display.flip()
            clock.tick(60)

        # Jeśli użytkownik coś wpisał, zapisz do pliku
        if user_name != "":
            save_to_excel(user_name, ending_time, self.player.total_jumps, self.current_level)

        # Czekanie na spację
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:

                    waiting = False

            # Wyświetlanie tego samego tła i tekstów
            self.screen.blit(background, (0, 0))
            self.win_banner2.draw(self.screen)
            self.win_banner.draw(self.screen)
            self.screen.blit(time_text, ((self.screen.get_width() * 0.41), self.screen.get_height() * 0.3 + 50))
            self.screen.blit(jumps_text, ((self.screen.get_width() * 0.41), self.screen.get_height() * 0.3 + 100))
            self.screen.blit(username_text, ((self.screen.get_width() * 0.405), self.screen.get_height() * 0.3 + 200))
            self.screen.blit(end1_text, ((self.screen.get_width() * 0.425), self.screen.get_height() * 0.3 + 350))
            self.screen.blit(end2_text, ((self.screen.get_width() * 0.415), self.screen.get_height() * 0.3 + 365))
            self.screen.blit(leaderboard_text, ((self.screen.get_width() * 0.45), self.screen.get_height() * 0.3 + 400))

            best_players = 0
            players = load_from_excel(self.current_level)
            while best_players < 3 and best_players < len(players):
                print(best_players + 1, ". ", players[best_players])
                player_str = f"{best_players + 1}. {players[best_players]}"
                players_text = font_10.render(player_str, True, textcolor)
                self.screen.blit(players_text, ((self.screen.get_width() * 0.42),
                                                self.screen.get_height() * 0.3 + 430 + best_players * 30))
                best_players += 1

            txt_surface = (font_20.render(user_name, True, textcolor))
            self.screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
            self.inputbox.draw(self.screen)

            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.screen.blit(cursor_img, (mouse_x - 30, mouse_y - 32))

            pygame.display.flip()
            clock.tick(60)

        self.main_menu()

    # Metoda do uruchomienia gry
    def run(self, level=None):
        # Sprawdza jaki level załadować
        gamePaused = False
        pygame.mouse.set_visible(False)
        # Wymiary przycisków jako % ekranu
        banner_w = RES_WIDTH * 0.3
        banner_h = RES_HEIGHT * 0.075
        button_w = RES_WIDTH * 0.2
        button_h = RES_HEIGHT * 0.06
        x_center = RES_WIDTH / 4 - button_w / 2

        # Skalowanie rozmiaru czcionki proporcjonalnie do wysokości ekranu
        font_size = int(RES_HEIGHT * 0.025)
        banner_font_size = int(RES_HEIGHT * 0.035)

        # Pozycje przycisków (pionowo)
        spacing = RES_HEIGHT * 0.075
        y_start = RES_HEIGHT * 0.075
        self.resume_button = Button('Resume', x_center, y_start + spacing * 1, button_w, button_h,
                                    "data/images/banner_scroll_wide_thin.png", font_size=font_size, highlight=True)
        self.restart_button = Button('Restart', x_center, y_start + spacing * 2, button_w, button_h,
                                      "data/images/banner_scroll_wide_thin.png", font_size=font_size, highlight=True)
        self.menu_button = Button('Main menu', x_center, y_start + spacing * 3, button_w, button_h,
                                     "data/images/banner_scroll_wide_thin.png", font_size=font_size - 2, highlight=True)
        self.quit_button = Button('Quit', x_center, y_start + spacing * 4, button_w, button_h,
                                  "data/images/banner_scroll_wide_thin.png", font_size=font_size, highlight=True)
        # Przycisk PAUSED jako banner (bez akcji, tylko wizualnie)
        self.paused_banner = Button('PAUSED', RES_WIDTH / 4 - banner_w / 2, RES_HEIGHT * 0.0375, banner_w, banner_h,
                                    "data/images/banner_scroll_wide_thin.png", font_size=banner_font_size,
                                    highlight=False)

        if level is not None:
            self.tilemap.load("data/map/" + str(level) + ".json")
            self.start_time = pygame.time.get_ticks()

        # Główna pętla gry
        while True:
            # Event handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        gamePaused = not gamePaused  # przełączanie pauzy

                    if not gamePaused:
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

                elif event.type == pygame.KEYUP and not gamePaused:
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

                elif event.type == pygame.MOUSEBUTTONDOWN and gamePaused:
                    mouse_pos = Button.get_scaled_mouse_pos(self, self.screen, self.display)
                    self.audio.play_sound("data/audio/click.wav")
                    if self.resume_button.is_clicked(mouse_pos=mouse_pos):
                        gamePaused = False
                    elif self.menu_button.is_clicked(mouse_pos=mouse_pos):
                        self.main_menu()
                    elif self.restart_button.is_clicked(mouse_pos=mouse_pos):
                        del self.player
                        self.player = Player(self, self.player_startpos, (16, 28))
                        self.run(level)
                    elif self.quit_button.is_clicked(mouse_pos=mouse_pos):
                        pygame.quit()
                        sys.exit()

            # Sprawdzenie, czy gracz wygrał
            if self.player.win:
                self.display_summary(time_str)
                elapsed_time = 0
                pygame.display.update()
            else:
                # Tlo dynamiczne
                self.display.blit(pygame.transform.scale(self.assets[self.current_level],
                                                         (self.display.get_width(), self.display.get_height())), (0, 0))

                if not gamePaused:
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

                    render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

                    # Rysowanie paska siły skoku
                    if self.player.jumping:
                        jump_duration = time.time() - self.player.jump_start_time
                        temp_power = min(jump_duration, self.player.max_jump_power)
                        filled_width = int(42 * (temp_power / self.player.max_jump_power))

                        # Rozmiar paska ładowania (wewnętrzny, kolorowy)
                        bar_width = 42
                        bar_height = 5

                        # Rozmiar ramki (tekstury)
                        border_surface = self.assets["bar_jumping"]
                        border_width, border_height = border_surface.get_size()

                        # Oblicz pozycję ramki
                        border_x = self.player.rect().centerx - render_scroll[0] - border_width // 2
                        border_y = self.player.rect().top - render_scroll[1] - border_height - 5  # lekko nad graczem

                        # Oblicz pozycję wewnętrznego paska (wycentrowanego w ramce)
                        bar_x = border_x + (border_width - bar_width) // 2
                        bar_y = border_y + (border_height - bar_height) // 2

                        # Kolorowy pasek (gradient zielony → czerwony)
                        ratio = temp_power / self.player.max_jump_power
                        red = int(255 * ratio)
                        green = int(255 * (1 - ratio))
                        color = (red, green, 0)

                        # Wypełniony fragment
                        pygame.draw.rect(self.display, color, (bar_x, bar_y, filled_width, bar_height))

                        # Szary fragment niewypełniony
                        if filled_width < bar_width:
                            pygame.draw.rect(self.display, (128, 128, 128),
                                             (bar_x + filled_width, bar_y, bar_width - filled_width, bar_height))

                        # Na koniec: narysuj ramkę z tekstury
                        self.display.blit(border_surface, (border_x, border_y))

                # Pauza
                if gamePaused:
                    mouse_pos = Button.get_scaled_mouse_pos(self, self.screen, self.display)
                    # 4 przyciski menu pauzy
                    # TODO: Naprawić by guziki działały

                    # Rysuj przyciski
                    self.paused_banner.draw(self.display)
                    self.resume_button.draw(self.display, mouse_pos=mouse_pos)
                    self.menu_button.draw(self.display, mouse_pos=mouse_pos)
                    self.restart_button.draw(self.display, mouse_pos=mouse_pos)
                    self.quit_button.draw(self.display, mouse_pos=mouse_pos)

                # Wyświetlenie wszystkiego na ekran
                self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))

                if gamePaused:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self.screen.blit(self.cursor_image, (mouse_x - 30, mouse_y - 32))

                if not gamePaused:
                    self.screen.blit(time_text, (10, 10))
                pygame.display.update()
                self.clock.tick(60)  # ograniczenie do 60fps

    # Metoda do skalowania obrazu w stylu pixel art bez rozmycia
    def _scale_pixel_art_image(self, image, target_width, target_height):
        # Wyłącz wygładzanie
        pygame.display.set_mode((RES_WIDTH, RES_HEIGHT), pygame.HWSURFACE)
        pygame.transform.set_smoothscale_backend('GENERIC')

        # Pobierz oryginalne wymiary
        original_width, original_height = image.get_size()

        # Znajdź największy możliwy mnożnik całkowity
        scale_x = target_width // original_width
        scale_y = target_height // original_height
        scale = max(1, min(scale_x, scale_y))

        # Najpierw skaluj przez mnożnik całkowity (zachowuje ostre piksele)
        if scale > 1:
            intermediate_size = (original_width * scale, original_height * scale)
            intermediate = pygame.transform.scale(image, intermediate_size)
        else:
            intermediate = image

        # Następnie skaluj do dokładnego rozmiaru
        final_image = pygame.transform.scale(intermediate, (target_width, target_height))
        return final_image


if __name__ == "__main__":
    Game().main_menu()