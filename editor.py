import pygame
import sys
from scripts.utility import load_images
from scripts.tilemap import Tilemap

RENDER_SCALE_X = 2
RENDER_SCALE_Y = 2
RES_WIDTH = 1920
RES_HEIGHT = 1080

class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Editor")
        self.screen = pygame.display.set_mode((RES_WIDTH, RES_HEIGHT))
        self.display = pygame.Surface((RES_WIDTH/2, RES_HEIGHT/2))

        self.clock = pygame.time.Clock()

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

        }

        self.movement = [False, False, False, False]

        self.tilemap = Tilemap(self, tile_size=16)

        try:
            self.tilemap.load("data/map/Galactic Tower.json")
        except FileNotFoundError:
            pass

        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True

    def run(self):
        # Główna pętla gry
        while True:
            # Tlo
            self.display.fill((0, 0, 0))

            self.scroll[0] += (self.movement[1] - self.movement[0]) * 3
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 3

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)
            self.tilemap.render_offset(self.display, offset=render_scroll)

            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)

            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE_X, mpos[1] / RENDER_SCALE_Y)

            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                        int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))

            if self.ongrid:
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                                                     tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_img, mpos)

            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                    "type": self.tile_list[self.tile_group], "variant": self.tile_variant, "pos": tile_pos}

            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile["type"]][tile["variant"]]
                    tile_r = pygame.Rect(tile["pos"][0] - self.scroll[0], tile["pos"][1] - self.scroll[1],
                                         tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)
            self.display.blit(current_tile_img, (5, 5))
            # Event handeler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append(
                                {"type": self.tile_list[self.tile_group], "variant": self.tile_variant,
                                 "pos": (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(
                                self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(
                                self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_p:
                        self.right_clicking = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_o:
                        self.tilemap.save("data/map/Galactic Tower.json")
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_p:
                        self.right_clicking = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False

            # if self.player.jumping:
            #     pygame.draw.rect(self.display, (0, 0, 0), self.player.rect())

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)  # ograniczenie do 60fps


Editor().run()
