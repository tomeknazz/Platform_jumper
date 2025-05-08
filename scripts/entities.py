import time
import pygame


# Klasa do stworzenia entity
class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        # Podstawowe i potrzebne atrybuty
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {"up": False, "down": False, "right": False, "left": False}
        self.collide_type_bottom = ""
        self.jumping = False
        self.action = ""
        self.animation = None
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action("idle")
        self.jumped = 0
        self.last_movement = None
        self.snow = False

    # Metoda tworząca hitbox gracza
    def rect(self):
        if self.jumping and self.velocity[1] < 0:
            # Zwróć mniejszy hitbox w trakcie skoku
            return pygame.Rect(self.pos[0], self.pos[1], self.size[0] - 5, self.size[1] - 5)
        else:
            # Zwróć normalny hitbox, kiedy nie w trakcie skoku
            return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    # Metoda sprawdzająca i ustawiająca akcje gracza (skok, bieg, idle, kucanie)
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + "/" + self.action].copy()

    # Metoda update'ująca gracza
    def update(self, tilemap, movement=(0, 0)):
        # Reset kolizji
        self.collisions = {"up": False, "down": False, "right": False, "left": False}
        # Ruch gracza ustawiony poprzez listę movement
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        # Ustawienie pozycji w osi x
        # + sprawdzenie, czy w śniegu
        if self.snow and not self.jumping:
            self.velocity[0] = 0
        else:
            self.pos[0] += frame_movement[0]

        # stworzenie hitboxu
        entity_rect = self.rect()
        # Fizyka os x
        for rect in tilemap.physics_rects(self.pos):
            if entity_rect.colliderect(rect[0]):
                if frame_movement[0] > 0:
                    entity_rect.right = rect[0].left
                    self.collisions["right"] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect[0].right
                    self.collisions["left"] = True
                self.pos[0] = entity_rect.x
        # Ustawienie pozycji os y
        self.pos[1] += frame_movement[1]
        # Hitbox
        entity_rect = self.rect()
        # Fizyka os y
        for rect in tilemap.physics_rects(self.pos):
            if entity_rect.colliderect(rect[0]):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect[0].top
                    self.collide_type_bottom = rect[1]
                    self.collisions["down"] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect[0].bottom
                    self.collisions["up"] = True
                self.pos[1] = entity_rect.y
        # Obrót postaci lewo/prawo
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        # Fizyka os y spowalnianie spadku w dół
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        # Resetowanie prędkości po kolizji od gory albo dolu
        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0
        # Aktualizacja animacji
        self.animation.update()

    # Renderowanie gracza
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))


# Klasa dedykowana dla gracza
class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        # Skorzystanie z już wcześniej napisanej klasy
        super().__init__(game, "player", pos, size)
        # Dodatkowe atrybuty
        self.air_time = 0
        self.bounce = False
        self.jumps = 1
        self.jump_time = 0
        self.win = False
        self.total_jumps = 0

    # Metoda do update'tu gracza
    def update(self, tilemap, movement=(0, 0)):
        # Skopiowanie metody update z poprzedniej klasy
        super().update(tilemap, movement=movement)
        # Sprawdzanie, z jakim typem bloku występuje kolizja
        # i działanie w trakcie kolizji z blokiem od dołu
        self.air_time += 1
        if self.collisions["down"]:
            self.air_time = 0
            self.jumps = 1
            if self.jumped == 1:
                self.jumping = False
                self.jumped = 0
            if self.collide_type_bottom == "ice":  # LÓD
                # Ślizganie się po lodzie
                if self.velocity[0] > 0:
                    self.velocity[0] = max(0, self.velocity[0] - 0.2)
                elif self.velocity[0] < 0:
                    self.velocity[0] = min(0, self.velocity[0] + 0.2)
                self.snow = False
            elif self.collide_type_bottom == "grass_thick_snow":
                self.snow = True
            elif self.collide_type_bottom == "win_tiles":
                self.win = True
            else:
                self.snow = False
                self.velocity[0] = 0

        # Odbicie od ściany w trakcie skoku
        if self.collisions["right"] and self.air_time > 4:
            self.velocity[0] = -1.8
        elif self.collisions["left"] and self.air_time > 4:
            self.velocity[0] = 1.8

        # Zmiana offsetu animacji dla kucania z powodu mniejszego rozmiaru png
        if self.action == "crouch":
            self.anim_offset = list(self.anim_offset)
            self.anim_offset[1] = 7
            self.anim_offset = tuple(self.anim_offset)
        else:
            self.anim_offset = list(self.anim_offset)
            self.anim_offset[1] = -3
            self.anim_offset = tuple(self.anim_offset)

        # Ustawianie animacji gracza
        if self.air_time > 4:
            self.set_action("jump")
        elif movement[0] != 0:
            self.set_action("run")
        elif self.jumping and self.air_time == 0:
            self.set_action("crouch")
        elif not self.jumping and movement[0] == 0:
            self.set_action("idle")

        # Sprawdzanie jak długo gracz trzyma strzałkę i gdy czas dotrze do max = 0.8 automatycznie skacze
        if self.jumping:
            t_now = time.time()
            if t_now - self.jump_time >= 0.8:
                self.jump(0.8)
            if self.last_movement == 0:
                self.flip = False
            if self.last_movement == 1:
                self.flip = True

    # Metoda do skoku
    def jump(self, power):
        if self.jumps == 1:
            self.velocity[1] = -4.5 * power
            if self.last_movement == 0:
                self.velocity[0] = 2
                self.flip = False
            if self.last_movement == 1:
                self.velocity[0] = -2
                self.flip = True
            self.jumped += 1
            self.jumps -= 1
            self.total_jumps += 1
            self.air_time = 5
            if self.collisions["down"]:
                self.last_movement = 2

