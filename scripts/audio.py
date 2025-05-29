import sys
import pygame


class Audio:
    def __init__(self, game):
        self.game = game
        self.sounds = {}
        self.music = None

    def load_sound(self, name):
        if name not in self.sounds:
            self.sounds[name] = pygame.mixer.Sound(self.game.assets[name])
        return self.sounds[name]

    def play_sound(self, name, volume=1.0):
        sound = self.load_sound(name)
        sound.set_volume(volume)
        sound.play()

    def load_music(self, name):
        if self.music != name:
            pygame.mixer.music.load(name)  # Load music directly from file path
            self.music = name

    def play_music(self, name, volume=1.0):
        if self.music != name or not pygame.mixer.music.get_busy():
            self.load_music(name)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)  # Loop indefinitely
