import sys
import math
import numpy as np
import random

# Send your busters out into the fog to trap ghosts and bring them home!

busters_per_player = int(input())  # the amount of busters you control
ghost_count = int(input())  # the amount of ghosts on the map
my_team_id = int(input())  # if this is 0, your base is on the top left of the map, if it is one, on the bottom right

id_ghost_min_turn_stamina = 0
ghosts_global = {}
list_id_ghosts_removed = []
hunter = []
last_pos_hunter = []
last_pos_catcher = []
last_bust_stamina = -1
id_ghost_min_turn_stamina = -1
catcher = []
id_ghost_traped = -1
support = []
MY_BASE = []
BASE_ENEMY = []
BASE_SUPPORT = []
NEXT_BASE_SUPPORT = []

hunter_enemy = []
catcher_enemy = []
support_enemy = []
busters_enemy = {}
turns_left_avant_stun = 0
id_ghost_released = -1
ghost_released = []
busting_ghost = []
number_busts = 0
trapped_id_ghost_enemy = -1
# support_target = []
is_radar = False
is_see_catcher_enemy = False

# print("My team ID: ", my_team_id, file=sys.stderr, flush=True)
if my_team_id:
    MY_BASE = [16000, 9000]
    BASE_ENEMY = [0,0]
    BASE_SUPPORT = [12000, 2250]
    NEXT_BASE_SUPPORT = [3000, 1250]
else:
    MY_BASE = [0,0]
    BASE_ENEMY = [16000, 9000]
    BASE_SUPPORT = [4000, 6750]
    NEXT_BASE_SUPPORT = [13000, 7750]

def distance(e1, e2):
    return math.floor(math.sqrt(abs(e2[0] - e1[0]) ** 2 + abs(e2[1] - e1[1]) ** 2))

def random_x():
    return random.randint(0,16000)

def random_y():
    return random.randint(0,9000)

# g = [state, x, y]
def ghost_symetric(g):
    return [41, 16000-g[1], 9000-g[2]]

def is_same_ghost(g1, g2):
    return distance(g1[1:3], g2[1:3]) < 400

def random_support_x():
    if my_team_id:
        return random.choice([2000, 2500, 3000])
    else:
        return random.choice([11500, 12000, 12500])

def random_support_y():
    if my_team_id:
        return random.choice([2000, 2500, 3000])
    else:
        return random.choice([5000, 5500, 6000])


# game loop
while True:
    entities = int(input())  # the number of busters and ghosts visible to you
    is_stuned = 0
    ghosts = {}
    last_pos_hunter = hunter
    last_pos_catcher = catcher
    if id_ghost_min_turn_stamina != -1 and id_ghost_min_turn_stamina in ghosts_global:
        last_bust_stamina = ghosts_global[id_ghost_min_turn_stamina][0]
    # print("Last Bust Hunter: ", last_bust_stamina, file=sys.stderr, flush=True)
    is_see_catcher_enemy = False

    for i in range(entities):
        # entity_id: buster id or ghost id
        # y: position of this buster / ghost
        # entity_type: the team id if it is a buster, -1 if it is a ghost.
        # entity_role: -1 for ghosts, 0 for the HUNTER, 1 for the GHOST CATCHER and 2 for the SUPPORT
        # state: For busters: 0=idle, 1=carrying a ghost. For ghosts: remaining stamina points.
        # value: For busters: Ghost id being carried/busted or number of turns left when stunned. For ghosts: number of busters attempting to trap this ghost.
        entity_id, x, y, entity_type, entity_role, state, value = [int(j) for j in input().split()]

        # print("Buster ID: ", entity_id)
        if entity_role == -1:
            print("Trouver ghost: ", (entity_id, x, y, state, value), file=sys.stderr, flush=True)
            ghosts[entity_id] = [state, x, y]
            ghosts_global[entity_id] = [state, x, y]
        
        if entity_type == my_team_id:
            if entity_role == 0:
                hunter = [state, x, y, value]
            if entity_role == 1:
                catcher = [state, x, y, value]
            if entity_role == 2:
                support = [state, x, y, value]
        
        elif entity_type == 1 - my_team_id:
            if entity_role == 0:
                hunter_enemy = [entity_id, state, x, y, value]
            if entity_role == 1:
                catcher_enemy = [entity_id, state, x, y, value]
                is_see_catcher_enemy = True
                if state == 1:
                    trapped_id_ghost_enemy = value
            if entity_role == 2:
                support_enemy = [entity_id, state, x, y, value]
            
            # busters_enemy[entity_id] = [state, x, y, value, entity_id, entity_role]
    
    for g_id in ghosts_global.copy():
        g_h_symetric = ghost_symetric(ghosts_global[g_id])
        g_id_symetric = 0
        if g_id == 0:
            g_id_symetric = g_id
        elif g_id % 2 == 0:
            g_id_symetric = g_id - 1
        else:
            g_id_symetric = g_id + 1

        if g_id_symetric not in ghosts_global and g_id_symetric not in list_id_ghosts_removed and g_id_symetric != g_id:
            ghosts_global[g_id_symetric] = g_h_symetric
    

    if id_ghost_released in ghosts_global:
        if id_ghost_released  == trapped_id_ghost_enemy:
            ghost_released = ghosts_global[id_ghost_released]
            del ghosts_global[id_ghost_released]
            
        else:
            if trapped_id_ghost_enemy in ghosts_global:
                del ghosts_global[trapped_id_ghost_enemy]
                list_id_ghosts_removed.append(trapped_id_ghost_enemy)
    else:
        id_ghost_released = -1
        if trapped_id_ghost_enemy in ghosts_global:
            del ghosts_global[trapped_id_ghost_enemy]
            list_id_ghosts_removed.append(trapped_id_ghost_enemy)
    

    if ghosts or ghosts_global:
        ghosts_global.update(ghosts)
        id_ghost_min_turn_stamina = min(ghosts_global.keys(), key=(lambda g: ghosts_global[g][0]))
        min_turn_stamina = min([v[0] for v in ghosts_global.values()])
        list_id_ghosts_min_turn_stamina = [k for k, v in ghosts_global.items() if v[0] == min_turn_stamina]
        # print("List id ghost minimales: ", list_id_ghosts_min_turn_stamina, file=sys.stderr, flush=True)

        min_distance = distance(ghosts_global[id_ghost_min_turn_stamina][1:3], hunter[1:3])
        id_ghost_min_turn_stamina = list_id_ghosts_min_turn_stamina[0]
        for g in list_id_ghosts_min_turn_stamina:
            if min_distance > distance(ghosts_global[g][1:3], hunter[1:3]):
                min_distance = distance(ghosts_global[g][1:3], hunter[1:3])
                id_ghost_min_turn_stamina = g

        h_x = ghosts_global[id_ghost_min_turn_stamina][1]
        h_y = ghosts_global[id_ghost_min_turn_stamina][2]
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr, flush=True)

    for g_id in ghosts_global.copy():
        print("ghost global: ", (g_id, ghosts_global[g_id]), file=sys.stderr, flush=True)

    # First the HUNTER : MOVE x y | BUST id
    # Second the GHOST CATCHER: MOVE x y | TRAP id | RELEASE
    # Third the SUPPORT: MOVE x y | STUN id | RADAR
    print("Position hunter: ", hunter[1:3], file=sys.stderr, flush=True)

    # Hunter and Catcher
    if ghosts_global:
        if 900 < distance(hunter[1:3], [h_x,h_y]) < 1760:
            print("remaining stamina points:  ", ghosts_global[id_ghost_min_turn_stamina][0], file=sys.stderr, flush=True)
            # If mana = 0
            if ghosts_global[id_ghost_min_turn_stamina][0] > 0:
                print("Now Bust Hunter: ", ghosts_global[id_ghost_min_turn_stamina][0], file=sys.stderr, flush=True)
                print("Distance Hunter between ghost: ", distance(hunter[1:3], [h_x,h_y]), file=sys.stderr, flush=True)
                print("BUST ", id_ghost_min_turn_stamina)
                
                if number_busts % 2 == 0:
                    if busting_ghost:
                        busting_ghost[0] = [id_ghost_min_turn_stamina, ghosts_global[id_ghost_min_turn_stamina][0]]
                    else:
                        busting_ghost.append([id_ghost_min_turn_stamina, ghosts_global[id_ghost_min_turn_stamina][0]])
                else:
                    if len(busting_ghost) == 1:
                        busting_ghost.append([id_ghost_min_turn_stamina, ghosts_global[id_ghost_min_turn_stamina][0]])
                    else:
                        busting_ghost[1] = [id_ghost_min_turn_stamina, ghosts_global[id_ghost_min_turn_stamina][0]]
                number_busts += 1
                if len(busting_ghost) == 2:
                    if busting_ghost[0][0] == busting_ghost[1][0] and busting_ghost[0][1] == busting_ghost[1][1]:
                        del ghosts_global[id_ghost_min_turn_stamina]
                        list_id_ghosts_removed.append(id_ghost_min_turn_stamina)
            else:
                print("MOVE ", random_x(), random_y())
        else:
            if last_pos_hunter:
                if distance(hunter[1:3], last_pos_hunter[1:3]) > 0:
                    print("MOVE ", h_x, h_y)
                else:
                    print("MOVE ", random_x(), random_y())
                    # print("Delete ghost in global: ", id_ghost_min_turn_stamina, file=sys.stderr, flush=True)
                    # del ghosts_global[id_ghost_min_turn_stamina]
            else:
                # Hunter
                print("MOVE ", h_x, h_y)
                
        #Catcher
        print("Distance catcher: ", distance(catcher[1:3], [h_x,h_y]), file=sys.stderr, flush=True)

        if id_ghost_released == -1:
            if catcher[0] == 0:
                if 900 < distance(catcher[1:3], [h_x,h_y]) < 1760:
                    if id_ghost_min_turn_stamina in ghosts_global:
                        if ghosts_global[id_ghost_min_turn_stamina][0] == 0:
                            if distance(catcher[1:3], last_pos_catcher[1:3]) > 0:
                                print("TRAP ", id_ghost_min_turn_stamina)
                            else:
                                print("MOVE ", random_x(), random_y())
                                # del ghosts_global[id_ghost_min_turn_stamina]
                        else:
                            #print("MOVE 8000 4500")
                            print("MOVE ", random_x(), random_y())
                    else:
                        print("MOVE ", random_x(), random_y())
                    

                elif distance(catcher[1:3], [h_x,h_y]) <= 900:
                    # print("MOVE ", h_x, h_y)
                    print("MOVE ", random_x(), random_y())
                else:
                    print("MOVE ", h_x, h_y)
            else:
                if distance(catcher[1:3], MY_BASE) < 160:
                    if catcher[3] >= 0:
                        print("RELEASE ", catcher[3])
                        if catcher[3] in ghosts_global:
                            del ghosts_global[catcher[3]]
                        list_id_ghosts_removed.append(catcher[3])
                    else:
                        print("MOVE ", random_x(), random_y())
                else:
                    print("MOVE ", MY_BASE[0], MY_BASE[1])
        else:
            if catcher[0] == 0:
                print("Ghost released by enemy: ", id_ghost_released, file=sys.stderr, flush=True)
                if 900 < distance(catcher[1:3], ghost_released[1:3]) < 1760:
                    if distance(catcher[1:3], last_pos_catcher[1:3]) > 0:
                        print("TRAP ", id_ghost_released)
                    else:
                        id_ghost_released = -1
                        print("MOVE ", h_x, h_y)
                else:
                    print("MOVE ", ghost_released[1], ghost_released[2])
            else:
                if distance(catcher[1:3], MY_BASE) < 160:
                    if catcher[3] >= 0:
                        print("RELEASE ", catcher[3])
                        if catcher[3] in ghosts_global:
                            del ghosts_global[catcher[3]]
                        list_id_ghosts_removed.append(catcher[3])
                    else:
                        print("MOVE ", h_x, h_y)
                else:
                    print("MOVE ", MY_BASE[0], MY_BASE[1])
        
    else:
        # Hunter
        print("MOVE ", random_x(), random_y())

        # Catcher
        if catcher[3] >= 0:
            print("ID Ghost traped: ", catcher[3], file=sys.stderr, flush=True)
        
            if distance(catcher[1:3], MY_BASE) < 1600:
                print("RELEASE ", catcher[3])
                list_id_ghosts_removed.append(catcher[3])
                del ghosts_global[catcher[3]]
               
            else:
                print("MOVE ", MY_BASE[0], MY_BASE[1])
            
        else:
            print("MOVE ", random_x(), random_y())
        

    # Support
    if is_radar:
        if turns_left_avant_stun == 0:
            if not catcher_enemy:
                print("MOVE ", NEXT_BASE_SUPPORT[0], NEXT_BASE_SUPPORT[1])
            else:
                if is_see_catcher_enemy:
                    if distance(support[1:3], catcher_enemy[2:4]) < 1760:
                        # is_stuned = 1
                        print("Distance target stuneed: ", distance(support[1:3], catcher_enemy[2:4]), file=sys.stderr, flush=True)
                        # print("Target stunned: ", support_target, file=sys.stderr, flush=True)
                        print("STUN ", catcher_enemy[0], "Support stun")
                        turns_left_avant_stun = 19
                        if catcher_enemy[1] == 1:
                            if support_enemy:
                                if distance(catcher[1:3], support_enemy[2:4]) < 1760:
                                    id_ghost_released = -1
                                else:
                                    id_ghost_released = catcher_enemy[4]
                    else:
                        print("MOVE ", catcher_enemy[2], catcher_enemy[3])
                else:
                    print("MOVE ", NEXT_BASE_SUPPORT[0], NEXT_BASE_SUPPORT[1])
                
        else:
            turns_left_avant_stun -= 1
            print("MOVE ", catcher_enemy[2], catcher_enemy[3])
    else:
        if distance(support[1:3], BASE_SUPPORT) < 500:
            print("RADAR Support radar")
            is_radar = True
        else:
            # print("MOVE 8000 4500")
            print("MOVE ", BASE_SUPPORT[0], BASE_SUPPORT[1])
            

    # print("MOVE h_x h_y")
    # print("MOVE 8000 4500")