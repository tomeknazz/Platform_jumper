import pygame
import json

# Typy klocków, które mają kolizje
PHYSICS_TILES = {"grass", "stone", "Evil-Purple", "Pyramid-Yellow", "Emerald-Green",
                 "Diamond-Blue", "Castle-blue", "grass_purple", "grass_thick_snow", "plain_snow", "ice", "win_tiles"}


# Klasa dotycząca mapy klocków
class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []

    # Fizyka klocków(kolizja)
    def physics_rects(self, pos):
        rects = []
        for tile in self.tilemap:
            if self.tilemap[tile]["type"] in PHYSICS_TILES:
                rects.append(
                    [pygame.Rect(self.tilemap[tile]["pos"][0] * self.tile_size,
                                 self.tilemap[tile]["pos"][1] * self.tile_size, self.tile_size,
                                 self.tile_size), self.tilemap[tile]["type"]])
        return rects

    # Zapisywanie w json
    def save(self, path):
        f = open(path, "w")
        json.dump({"tilemap": self.tilemap, "tile_size": self.tile_size, "offgrid": self.offgrid_tiles}, f)
        f.close()

    # Wczytywanie z json
    def load(self, path):
        f = open(path, "r")
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data["tilemap"]
        self.tile_size = map_data["tile_size"]
        self.offgrid_tiles = map_data["offgrid"]

    # Renderowanie klocków w gridzie
    def render(self, surf, offset=(0, 0)):
        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ";" + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.assets[tile["type"]][tile["variant"]],
                              (
                                  tile["pos"][0] * self.tile_size - offset[0],
                                  tile["pos"][1] * self.tile_size - offset[1]))

    # Renderowanie klocków poza gridem
    def render_offset(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile["type"]][tile["variant"]],
                      (tile["pos"][0] - offset[0], tile["pos"][1] - offset[1]))
