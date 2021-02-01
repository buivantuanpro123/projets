import pygame, random, sys
from random import randint, uniform
from class_spore import *
from pygame.locals import *

WINDOWWIDTH = 600
WINDOWHEIGHT = 400
BOB_WIDTH = 10
BOB_HEIGHT = 18

FONT_SIZE = 30

SKY = (146, 244, 255)

TEXTCOLOR = (255, 0, 0)


# Load images from path ----------------------------------------------------- #
def load_img(path, params):
    if params.DISPLAY_GRAPHICALLY:
        img = pygame.image.load('data/images/' + path + '.png').convert()
    else:
        img = pygame.image.load('data/images/' + path + '.png')
    img.set_colorkey((255, 255, 255))
    return img


global animation_database
animation_database = {}
explosions = []


# Functions -------------------------------------------------- #
# flip a Surface(image) horizontally --------------------------#
def flip(img, boolean=True):
    return pygame.transform.flip(img, boolean, False)


# return a sequence of images for creating the effect of animations ----------------------#
def animation_sequence(sequence, base_path, colorkey=(255, 255, 255), transparency=255):
    global animation_database
    result = []
    for frame in sequence:
        image_id = base_path + str(frame[0])
        image = pygame.image.load(image_id + '.png').convert()
        image.set_colorkey(colorkey)
        image.set_alpha(transparency)
        animation_database[image_id] = image.copy()
        for i in range(frame[1]):
            result.append(image_id)
    return result


# create a bob_graphic --------------------------------------------------------#
def init_bob_graphic(params):
    bob_graphic = Bob_graphic(params)
    return bob_graphic


class Tile:
    def __init__(self, env_type, params):
        if (env_type == params.BIOMES["field"]):
            self.image = load_img('tiles/grass', params)
        if (env_type == params.BIOMES["desert"]):
            self.image = load_img('tiles/desert', params)
        if (env_type == params.BIOMES["forest"]):
            self.image = load_img('tiles/forest', params)
        if (env_type == params.BIOMES["swamp"]):
            self.image = load_img('tiles/swamp', params)

        if (env_type == "lava"):
            self.image = load_img('tiles/lava', params)

        self.width = 0
        self.height = 0
        self.x = 0
        self.y = 0

        self.explosion_list = None
        self.animation_frame = 0
        self.flip = False
        self.animation = False

    # get width, height of a image of tile -----------------------------------------#    
    def get_rect(self):
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    # change image(frame) in the sequence of images explosion_list -------------------#
    def change_frame(self, amount):
        self.animation_frame += amount
        if self.explosion_list != None:
            while self.animation_frame < 0:
                self.animation_frame += len(self.explosion_list)
            while self.animation_frame >= len(self.explosion_list):
                self.animation_frame -= len(self.explosion_list)

    # get current image at position animation_frame in explosion_list and flip it -------------#
    def get_current_img(self):
        if self.explosion_list == None:
            if self.image != None:
                return flip(self.image, self.flip)
            else:
                return None
        else:
            return flip(animation_database[self.explosion_list[self.animation_frame]], self.flip)


class Bob_graphic:
    def __init__(self, params):
        self.image = load_img('bobs/stand_f', params)
        self.width = BOB_WIDTH
        self.height = BOB_HEIGHT
        self.rect = (0, 0, BOB_WIDTH, BOB_HEIGHT)
        self.walk_direction_list = None
        self.animation_frame = 0
        self.flip = False
        self.nb_action = 0
        self.movement = [0, 0]
        self.x = 0
        self.y = 0
        self.pos = 0

    # set the direction to flip --------------------------------------------#
    def set_flip(self, boolean):
        self.flip = boolean

    # change image(frame) in the sequence of images walk_direction_list -------------------#
    def change_frame(self, amount):
        self.animation_frame += amount
        if self.walk_direction_list != None:
            while self.animation_frame < 0:
                self.animation_frame += len(self.walk_direction_list)
            while self.animation_frame >= len(self.walk_direction_list):
                self.animation_frame -= len(self.walk_direction_list)

    # get current image at position animation_frame in walk_direction_list and flip it -------------#
    def get_current_img(self):
        if self.walk_direction_list == None:
            if self.image != None:
                return flip(self.image, self.flip)
            else:
                return None
        else:
            return flip(animation_database[self.walk_direction_list[self.animation_frame]], self.flip)

    # move le bob to a delta distance movement --------------------------------------------#
    def delta_move(self, movement):
        self.x += movement[0]
        self.y += movement[1]

    # reproduce a bob in bob_list_graphic ---------------------------------------------#
    def reproduce(self, bob_list, bob_list_graphic, params):
        new_bob_graphic = Bob_graphic(params)
        new_bob_graphic.x = bob_list[len(bob_list) - 1].coordinates.x
        new_bob_graphic.y = bob_list[len(bob_list) - 1].coordinates.y
        new_bob_graphic.width = int(BOB_WIDTH * (bob_list[len(bob_list) - 1].mass ** (1. / 3.)))
        new_bob_graphic.height = int(BOB_HEIGHT * (bob_list[len(bob_list) - 1].mass ** (1. / 3.)))
        new_bob_graphic.image = pygame.transform.scale(self.image, (new_bob_graphic.width, new_bob_graphic.height))
        bob_list_graphic.append(new_bob_graphic)


class Graphic:

    def __init__(self, params):
        # Setup pygame/window ---------------------------------------- #
        self.mainClock = pygame.time.Clock()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption('World of Bob')
        self.window_width = WINDOWWIDTH
        self.window_height = WINDOWHEIGHT
        self.display_width = params.DISPLAY_WIDTH
        self.display_height = params.DISPLAY_HEIGHT
        self.screen = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT), 0, 32)
        self.display = pygame.Surface((params.DISPLAY_WIDTH, params.DISPLAY_HEIGHT))
        self.font_size = FONT_SIZE
        self.time_count = 0
        self.tick = 0
        self.day = 0
        self.font = pygame.font.SysFont('agencyfb', FONT_SIZE)
        self.added_foods = 0

        # Audio ------------------------------------------------------ #
        pygame.mixer.music.load('data/music/main.wav')

        # Tile images -------------------------------------------------------#
        self.tile_grass = Tile(params.BIOMES["field"], params)
        self.tile_desert = Tile(params.BIOMES["desert"], params)
        self.tile_forest = Tile(params.BIOMES["forest"], params)
        self.tile_swamp = Tile(params.BIOMES["swamp"], params)
        self.tile_lava = Tile("lava", params)

        self.tile_lava_list = [Tile("lava", params) for _ in range(((params.LAVA_AREA * params.N) // 100) ** 2)]

        # food images -------------------------------------------------------#
        self.food_image = load_img('foods/cherry', params)

        # bob images -------------------------------------------------------#
        self.bob_image = load_img('bobs/stand_f', params)

        # Scroll -------------------------------------------------------#
        self.scroll_x = -14 * params.N
        self.scroll_y = -4 * params.N
        self.paused = False
        self.scrollRight = False
        self.scrollLeft = False
        self.scrollUp = False
        self.scrollDown = False

        # Animation --------------------------------------------------#
        self.animation = False
        self.bob_walk_f = animation_sequence([[0, 3], [1, 2], [2, 3], [1, 2]], 'data/images/bobs/walk_f_')
        self.bob_walk_b = animation_sequence([[0, 3], [1, 2], [2, 3], [1, 2]], 'data/images/bobs/walk_b_')
        self.explosion_anim = animation_sequence([[0, 3], [1, 2], [2, 3], [3, 2]], 'data/images/explosion/explosion_')

    # draw Text onto the surface screen ------------------------------------------------------- #
    def drawText(self, text, x, y):
        textobj = self.font.render(text, 1, TEXTCOLOR)
        textrect = textobj.get_rect()
        textrect.topleft = (x, y)
        self.screen.blit(textobj, textrect)

    # terminate(quit) window pygame ---------------------------------------------#
    def terminate(self):
        pygame.quit()
        sys.exit()

    # Render Tiles --------------------------------------------------------#
    def render_tiles(self, world, params):
        i = 0
        for tiles in world.tiles:
            for tile in tiles:
                # render tiles: field, desert, forest, swamp onto the surface display ------------------#
                if tile.env_type == params.BIOMES["field"]:
                    self.display.blit(self.tile_grass.image,
                                      (tile.coordinates.x * 14 - tile.coordinates.y * 14 - int(self.scroll_x),
                                       tile.coordinates.x * 7 + tile.coordinates.y * 7 - int(self.scroll_y)))
                if tile.env_type == params.BIOMES["desert"]:
                    self.display.blit(self.tile_desert.image,
                                      (tile.coordinates.x * 14 - tile.coordinates.y * 14 - int(self.scroll_x),
                                       tile.coordinates.x * 7 + tile.coordinates.y * 7 - int(self.scroll_y)))
                if tile.env_type == params.BIOMES["forest"]:
                    self.display.blit(self.tile_grass.image,
                                      (tile.coordinates.x * 14 - tile.coordinates.y * 14 - int(self.scroll_x),
                                       tile.coordinates.x * 7 + tile.coordinates.y * 7 - int(self.scroll_y)))
                    self.display.blit(self.tile_forest.image,
                                      (tile.coordinates.x * 14 - tile.coordinates.y * 14 - int(self.scroll_x) + 3,
                                       tile.coordinates.x * 7 + tile.coordinates.y * 7 - int(self.scroll_y) - 17))
                if tile.env_type == params.BIOMES["swamp"]:
                    self.display.blit(self.tile_swamp.image,
                                      (tile.coordinates.x * 14 - tile.coordinates.y * 14 - int(self.scroll_x),
                                       tile.coordinates.x * 7 + tile.coordinates.y * 7 - int(self.scroll_y)))

                if (tile.lava):
                    # Animation of the explosion of lava onto the surface display ----------------------------------#
                    if (self.animation):
                        tile_lava = self.tile_lava_list[i]
                        i += 1
                        tile_lava.explosion_list = self.explosion_anim
                        if (self.animation):
                            if (not self.paused):
                                tile_lava.change_frame(1)
                            self.display.blit(tile_lava.get_current_img(),
                                              (tile.coordinates.x * 14 - tile.coordinates.y * 14 - int(self.scroll_x),
                                               tile.coordinates.x * 7 + tile.coordinates.y * 7 - int(self.scroll_y)))
                            if (tile_lava.animation_frame == 9):
                                tile.lava = False
                    else:
                        # render tile lava for version non animation onto the surface display --------------------------#
                        self.display.blit(self.tile_lava.image,
                                          (tile.coordinates.x * 14 - tile.coordinates.y * 14 - int(self.scroll_x),
                                           tile.coordinates.x * 7 + tile.coordinates.y * 7 - int(self.scroll_y)))

    # Render Foods onto the surface display ----------------------------------------------------------#
    def render_foods(self, world):
        for tiles in world.tiles:
            for tile in tiles:
                if tile.qtyFood > 0:
                    self.display.blit(self.food_image,
                                      (tile.coordinates.x * 14 - tile.coordinates.y * 14 + 9 - int(self.scroll_x),
                                       tile.coordinates.x * 7 + tile.coordinates.y * 7 - int(self.scroll_y)))

    # Render Bobs onto the surface display ------------------------------------------------------------#
    def render_bobs(self, world, bob_list, bob_list_graphic, params):
        u = 0
        while (u < len(bob_list)):
            bob = bob_list[u]
            bob_graphic = bob_list_graphic[u]
            # Animation of the walk of bob onto the surface display ----------------------#
            if (self.animation):
                if (not self.paused):
                    bob_graphic.change_frame(1)
                bob_graphic.image = pygame.transform.scale(bob_graphic.get_current_img(),
                                                           (bob_graphic.width, bob_graphic.height))
                x = bob_graphic.x
                y = bob_graphic.y
                render_x = x * 14 - y * 14 + bob_graphic.width
                render_y = x * 7 + y * 7 - bob_graphic.height / 2
                self.display.blit(bob_graphic.image, (render_x - self.scroll_x, render_y - self.scroll_y))
                if (not self.paused):
                    bob_graphic.delta_move(bob_graphic.movement)

                if (bob_graphic.x == int(bob_graphic.x) and bob_graphic.y == int(bob_graphic.y)):
                    bob.boba_fedd(world, params)

            else:
                # render bob for version non animation onto the surface display ----------------------#
                bob_graphic.image = pygame.transform.scale(self.bob_image, (bob_graphic.width, bob_graphic.height))
                x = bob.coordinates.x
                y = bob.coordinates.y
                render_x = x * 14 - y * 14 + 9
                render_y = x * 7 + y * 7 - 10
                self.display.blit(bob_graphic.image, (render_x - self.scroll_x, render_y - self.scroll_y))
            u += 1

    # new foods at the begin of the day ----------------------------------------# 
    def add_foods(self, world, food_list, params):
        """ add_food permet d'initialiser la liste de nourriture et la reinitialise apres chaque jour """
        if self.tick == 0 and self.added_foods == 0:
            self.day += 1
            food_list.add_food(world, params)
            self.added_foods += 1
        if self.tick == params.NB_TICK - 1:
            self.added_foods = 0

    # buttons in pygame --------------------------------------------------------#
    def button(self, params):
        # Buttons ---------------------------------------------------------#
        for event in pygame.event.get():  # get events from the user
            # the user clicks the window's "X" button: terminate the program -----------------------------#
            if event.type == QUIT:
                self.terminate()

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:  # it is key Echap
                    self.terminate()

                # the user click p on keyboard: pause window  --------------------------------------#
                if event.key == K_p:
                    self.paused = not self.paused

                # the user click z on keyboard: return initial state before zooming --------------------------------------#
                if event.key == K_z:  # w in keyboard of france
                    self.display = self.display.get_abs_parent()

                # the user click s on keyboard: return initial state before scrolling --------------------------------------#
                if event.key == K_s:
                    self.scroll_x = -14 * params.N
                    self.scroll_y = -4 * params.N

                # the user click the right arrow on keyboard: right scroll --------------------------------------#
                if event.key == K_RIGHT:
                    self.scrollRight = True

                # the user click the left arrow on keyboard: left scroll --------------------------------------#
                if event.key == K_LEFT:
                    self.scrollLeft = True

                # the user click the up arrow on keyboard: up scroll --------------------------------------#
                if event.key == K_UP:
                    self.scrollUp = True

                # the user click the down arrow on keyboard: down scroll --------------------------------------#
                if event.key == K_DOWN:
                    self.scrollDown = True

                # the user click F11 on keyboard: resize window  --------------------------------------#
                if event.key == K_F11:
                    if self.window_width == 600:
                        self.window_width = 900
                        self.window_height = 600
                    else:
                        self.window_width = 600
                        self.window_height = 400
                    self.screen = pygame.display.set_mode((self.window_width, self.window_height), 0, 32)

            # Scroll ------------------------------------------------------#
            if event.type == KEYUP:
                if event.key == K_RIGHT:
                    self.scrollRight = False
                if event.key == K_LEFT:
                    self.scrollLeft = False
                if event.key == K_UP:
                    self.scrollUp = False
                if event.key == K_DOWN:
                    self.scrollDown = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                # the wheel is rolled up: zoom in -------------------------#
                if event.button == 4:
                    w = max(self.display.get_width() - 6 * params.N / 10, 10)
                    h = max(self.display.get_height() - 4 * params.N / 10, 10)
                    rect = pygame.Rect(0, 0, w, h)
                    self.display = self.display.subsurface(rect)
                    pygame.display.update()

                # the wheel is rolled down: zoom out -------------------------#
                if event.button == 5:
                    w = min(self.display.get_width() + 3 * params.N / 10, params.DISPLAY_WIDTH)
                    h = min(self.display.get_height() + 2 * params.N / 10, params.DISPLAY_HEIGHT)
                    rect = pygame.Rect(0, 0, w, h)
                    if (self.display.get_parent() != None):
                        self.display = self.display.get_parent()
                    pygame.display.update()

        # Scroll -------------------------------------------------------#
        if self.scrollRight:
            self.scroll_x += 5 * params.N / 10
        if self.scrollLeft:
            self.scroll_x -= 5 * params.N / 10
        if self.scrollUp:
            self.scroll_y -= 5 * params.N / 10
        if self.scrollDown:
            self.scroll_y += 5 * params.N / 10

    # draw time(tick, day) onto the surface screen -----------------------------------#
    def draw_time(self, nb_tick, nb_day):
        tick = "TICK:" + str(nb_tick)
        day = "DAY:" + str(nb_day)
        self.drawText(tick, 10, 0)
        self.drawText(day, 10, FONT_SIZE)

    # pause the simulation ----------------------------------------------------#
    def paused_world(self, world, bob_list, bob_list_graphic, tick, day, params):
        while self.paused:
            # Background --------------------------------------------- #
            self.display.fill(SKY)
            self.render_tiles(world, params)
            self.render_foods(world)
            self.render_bobs(world, bob_list, bob_list_graphic, params)

            self.draw_time(tick, day)

            self.button(params)
            self.update(tick, day)
            self.drawText("Paused", self.window_width / 2, self.window_height / 2)
            pygame.display.update()
            if (self.animation):
                # delay to keep the game running slower than the given ticks per second. -------------#
                # help limit the runtime speed of a game ----------------------------------------#
                self.mainClock.tick(params.FPS_anim)
            else:
                self.mainClock.tick(params.FPS_static)

    # update all the modifications of surface display onto surface screen ----------------------#
    def update(self, tick, day):
        self.screen.blit(pygame.transform.scale(self.display, (self.window_width, self.window_height)), (0, 0))
        self.draw_time(tick, day)
        pygame.display.update()

    # display the world of bob ---------------------------------------# 
    def display_world(self, world, bob_list, bob_list_graphic, tick, day, params):
        # Background --------------------------------------------- #
        self.display.fill(SKY)

        self.render_tiles(world, params)
        self.render_foods(world)
        self.render_bobs(world, bob_list, bob_list_graphic, params)

        self.button(params)
        self.paused_world(world, bob_list, bob_list_graphic, tick, day, params)
        self.update(tick, day)
        if (self.animation):
            # delay to keep the game running slower than the given ticks per second. -------------#
            # help limit the runtime speed of a game ----------------------------------------#
            self.mainClock.tick(params.FPS_anim)
        else:
            self.mainClock.tick(params.FPS_static)

    # animation stimulation the world of bob --------------------------------------#
    def animation_stimulation(self, world, bob_list, bob_list_graphic, food_list, params):

        self.add_foods(world, food_list, params)

        u = 0
        while (u < len(bob_list)):
            bob = bob_list[u]
            bob_graphic = bob_list_graphic[u]

            if (bob.energy <= 0):
                i = world.tiles[bob.coordinates.x][bob.coordinates.y].popBob.index(bob)
                del world.tiles[bob.coordinates.x][bob.coordinates.y].popBob[i]
                del bob_list[u]
                del bob_list_graphic[u]
                continue

            if (bob_graphic.x == int(bob_graphic.x) and bob_graphic.y == int(bob_graphic.y)):
                x = bob.coordinates.x
                y = bob.coordinates.y

                if (bob_graphic.nb_action == 0):
                    bob.current_velocity = bob.velocity + bob.velocity_buffer  # on commence le tick avec la velocite du bob
                    bob.velocity_buffer = bob.current_velocity - int(bob.current_velocity)
                    bob.current_velocity = int(bob.current_velocity)
                    bob_graphic.nb_action = bob.current_velocity


                if bob_graphic.nb_action >= 1:  # Tant que le bob a au moins un point de velocite, il peut faire une action
                    if (
                            bob.energy > 0):  # Si manage_energie retourne True (si le bob s'est reproduit ou est mort) on saute toutes les conditions suivantes
                        if not bob.manage_energy(world,
                                                 bob_list,
                                                 params):  # Si manage_energie retourne True (si le bob s'est reproduit ou est mort) on saute toutes les conditions suivantes
                            bob.look(world, params)
                            bob.memorise(world, params)
                            if world.tiles[bob.coordinates.x][
                                bob.coordinates.y].qtyFood > 0:  # Si il y a de la nourriture sur sa case il se nourrit
                                bob.energy -= 0.5
                                bob.boba_fedd(world, params)  # Le bob se nourrit
                                bob_graphic.movement = [0, 0]
                            else:  # Sinon il se deplace
                                if (not bob.hunt_or_be_hunted(world, params)):
                                    if bob.food_memory:
                                        # Le Bob se dirige vers la plus grande source de nourriture en memoire
                                        bob.theres_always_a_bigger_bob(bob.food_memory[0], world, params)
                                    else:
                                        bob.move(world, params, n=-1, tiles_to_avoid=bob.visited_tiles_memory)

                                    if (bob.coordinates.x > x):
                                        bob_graphic.movement = [0.0625 * bob.current_velocity, 0]
                                        bob_graphic.walk_direction_list = self.bob_walk_f
                                        bob_graphic.set_flip(False)
                                    elif (bob.coordinates.x < x):
                                        bob_graphic.movement = [-0.0625 * bob.current_velocity, 0]
                                        bob_graphic.walk_direction_list = self.bob_walk_b
                                        bob_graphic.set_flip(True)
                                    else:
                                        if (bob.coordinates.y > y):
                                            bob_graphic.movement = [0, 0.0625 * bob.current_velocity]
                                            bob_graphic.walk_direction_list = self.bob_walk_f
                                            bob_graphic.set_flip(True)
                                        elif (bob.coordinates.y < y):
                                            bob_graphic.movement = [0, -0.0625 * bob.current_velocity]
                                            bob_graphic.walk_direction_list = self.bob_walk_b
                                            bob_graphic.set_flip(False)
                                        else:
                                            bob_graphic.movement = [0, 0]
                                else:
                                    if (bob.coordinates.x > x):
                                        bob_graphic.movement = [0.0625 * bob.current_velocity, 0]
                                        bob_graphic.walk_direction_list = self.bob_walk_f
                                        bob_graphic.set_flip(False)
                                    elif (bob.coordinates.x < x):
                                        bob_graphic.movement = [-0.0625 * bob.current_velocity, 0]
                                        bob_graphic.walk_direction_list = self.bob_walk_b
                                        bob_graphic.set_flip(True)
                                    else:
                                        if (bob.coordinates.y > y):
                                            bob_graphic.movement = [0, 0.0625 * bob.current_velocity]
                                            bob_graphic.walk_direction_list = self.bob_walk_f
                                            bob_graphic.set_flip(True)
                                        elif (bob.coordinates.y < y):
                                            bob_graphic.movement = [0, -0.0625 * bob.current_velocity]
                                            bob_graphic.walk_direction_list = self.bob_walk_b
                                            bob_graphic.set_flip(False)
                                        else:
                                            bob_graphic.movement = [0, 0]

                                bob.energy -= (bob.mass * (bob.current_velocity ** 2)) + 0.2 * (
                                        bob.perception + bob.memory_points)

                            if len(world.tiles[x][y].popBob) >= 2:  # Si il y a plusieurs Bob sur la meme case
                                for i in world.tiles[x][y].popBob:
                                    bob.dual_of_fate(i, params)  # Ils essaient de se battre un par un

                        else:
                            bob_graphic.reproduce(bob_list, bob_list_graphic, params)
                            bob_graphic.movement = [0, 0]

                    bob_graphic.nb_action -= 1
                else:
                    bob_graphic.movement = [0, 0]
                    if (bob.current_velocity == 0):
                        bob.energy -= 0.5
            u += 1

        minutes = int(self.time_count / (16 * params.NB_TICK))
        tick = int(self.tick)
        self.tick = int((self.time_count - minutes * (16 * params.NB_TICK)) / 16)

        # lava ------------------------------------------------------#
        if (self.tick - tick == 1):
            if params.LAVA_RATE > 0:
                if round(uniform(0, 100), 5) <= params.LAVA_RATE:
                    floor_is_lava(world, bob_list, params)

        self.time_count += 1
        self.display_world(world, bob_list, bob_list_graphic, self.tick, self.day, params)
