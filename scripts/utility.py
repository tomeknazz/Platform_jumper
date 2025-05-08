import pygame
import os
import sys
from openpyxl import Workbook
from openpyxl import load_workbook


BASE_IMG_PATH = "data/images/"


# Załadowanie obrazka
def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img


# Załadowanie wielu obrazków
def load_images(path):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + "/" + img_name))
    return images


# Pobieranie inputu od gracza
def get_user_input(screen):
    font = pygame.font.Font(None, 64)
    input_box = pygame.Rect((screen.get_width() / 2) - 200, (screen.get_height() / 2.5 + 250), 140, 64)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        txt_surface = font.render(text, True, color)
        width = max(400, txt_surface.get_width() + 10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)
        pygame.display.flip()

    return text


# Zapisywanie do xlsx
def save_to_excel(user_name, time, total_jumps, level_beaten):
    filename = 'Ranking.xlsx'

    try:
        # Try to load the existing workbook
        wb = load_workbook(filename)
        ws = wb.active
    except FileNotFoundError:
        # If the workbook does not exist, create a new one
        wb = Workbook()
        ws = wb.active
        ws.title = "Ranking"
        ws.append(['User Name', 'Time', 'Total Jumps', "Map"])

    # Append the data
    ws.append([user_name, time, total_jumps, level_beaten])

    wb.save(filename)


# Klasa z animacjami
class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        # Atrybuty
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)

    # Update animacji
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        return self.images[int(self.frame / self.img_duration)]
