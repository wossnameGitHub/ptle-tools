from __future__ import annotations

import random
from collections.abc import Iterable, MutableMapping, Sequence
from enum import IntEnum
from itertools import starmap
from typing import NamedTuple

import CONFIGS
from lib.constants import *  # noqa: F403
from lib.transition_infos import Area, Exit


class Transition(NamedTuple):
    from_: int
    to: int


class Choice(IntEnum):
    CONNECT = 1
    INBETWEEN = 2


class BucketType(IntEnum):
    ORIGIN = 1
    REDIRECT = 2


class Priority(IntEnum):
    CLOSED = 1
    OPEN = 2

class Outpost(IntEnum):
    JUNGLE = 1000
    BURNING = 2000


temples = (
    LevelCRC.MONKEY_TEMPLE,
    LevelCRC.SCORPION_TEMPLE,
    LevelCRC.PENGUIN_TEMPLE,
)

water_levels = (
    LevelCRC.TWIN_OUTPOSTS_UNDERWATER,
    LevelCRC.FLOODED_CAVE,
    LevelCRC.MYSTERIOUS_TEMPLE,
)

one_way_exits = (
    # the White Valley geyser
    Transition(LevelCRC.WHITE_VALLEY, LevelCRC.MOUNTAIN_SLED_RUN),
    # the Apu Illapu Shrine geyser
    Transition(LevelCRC.APU_ILLAPU_SHRINE, LevelCRC.WHITE_VALLEY),
    # the Apu Illapu Shrine one-way door
    Transition(LevelCRC.MOUNTAIN_SLED_RUN, LevelCRC.APU_ILLAPU_SHRINE),
    # the Jungle Canyon waterfall
    Transition(LevelCRC.CAVERN_LAKE, LevelCRC.JUNGLE_CANYON),
)

closed_door_exits = (
    # These passages are blocked by literal closed doors
    Transition(Outpost.JUNGLE, LevelCRC.FLOODED_COURTYARD),
    Transition(LevelCRC.SCORPION_TEMPLE, LevelCRC.EYES_OF_DOOM),
    Transition(LevelCRC.MOUNTAIN_OVERLOOK, LevelCRC.EYES_OF_DOOM),
    Transition(LevelCRC.COPACANTI_LAKE, LevelCRC.VALLEY_OF_SPIRITS),
    Transition(LevelCRC.MOUNTAIN_SLED_RUN, LevelCRC.COPACANTI_LAKE),
    # Passage blocked by Stones
    Transition(LevelCRC.ST_CLAIRE_DAY, LevelCRC.FLOODED_COURTYARD),
    # Passage blocked by Ice Wall
    Transition(LevelCRC.EKKEKO_ICE_CAVERN, LevelCRC.VALLEY_OF_SPIRITS),
    # Passage blocked by reverse Spider Web
    Transition(LevelCRC.BATTERED_BRIDGE, LevelCRC.ALTAR_OF_HUITACA),
)

_possible_starting_areas = [
    area for area in ALL_TRANSITION_AREAS
    # Remove unwanted starting areas from the list of random possibilities
    if area not in {
        # These areas will instantly softlock you
        LevelCRC.APU_ILLAPU_SHRINE,  # Softlock prevention would shove you in the geyser anyway
        # These areas will give too much progression
        LevelCRC.ST_CLAIRE_DAY,  # gives TNT
        LevelCRC.ST_CLAIRE_NIGHT,  # gives all items + access to El Dorado
        LevelCRC.JAGUAR,  # sends to final bosses
        LevelCRC.PUSCA,  # sends to final bosses
        # Temples and Spirits are mostly equivalent, so we remove half of them here.
        # Spawning in a temple forces you to do the fight anyway. For convenience let's spawn
        # directly in the fight (it's also funnier to start the rando as the animal spirit).
        *temples,
        # Spawning in a Native Minigame is mostly equivalent to spawning in Native Village
        # as they are currently not randomized.
        LevelCRC.WHACK_A_TUCO,
        LevelCRC.TUCO_SHOOT,
        LevelCRC.RAFT_BOWLING,
        LevelCRC.PICKAXE_RACE,
        LevelCRC.KABOOM,
        # Cutscenes
        LevelCRC.PLANE_CUTSCENE,
        LevelCRC.VIRACOCHA_MONOLITHS_CUTSCENE,
    }
]

temp_disabled_exits = [
    # Mouth of Inti has 2 connections with Altar of Huitaca, which causes problems,
    # basically it's very easy to get softlocked by the spider web when entering Altar of Huitaca.
    # So for now just don't randomize it. That way runs don't just end out of nowhere.
    (LevelCRC.ALTAR_OF_HUITACA, LevelCRC.MOUTH_OF_INTI),
    (LevelCRC.MOUTH_OF_INTI, LevelCRC.ALTAR_OF_HUITACA),
]

bypassed_exits = [
    # The 2 CUTSCENE Levels are currently chosen to not be randomized.
    # As of right now both of these cutscenes are hijacked to be skipped entirely.
    (LevelCRC.JAGUAR, LevelCRC.PLANE_CUTSCENE),
    (LevelCRC.PLANE_CUTSCENE, LevelCRC.CRASH_SITE),
    (LevelCRC.SPINJA_LAIR, LevelCRC.VIRACOCHA_MONOLITHS_CUTSCENE),
    (LevelCRC.VIRACOCHA_MONOLITHS_CUTSCENE, LevelCRC.VIRACOCHA_MONOLITHS),
    # This specific one-time, one-way warp is not randomized.
    # Instead this transition is manually hijacked to send you to Mysterious Temple instead.
    (LevelCRC.ALTAR_OF_AGES, LevelCRC.BITTENBINDERS_CAMP),
]

disabled_exits = (
    *temp_disabled_exits,
    *bypassed_exits,
    # The 3 Spirit Fights are not randomized,
    # because that causes issues with the transformation cutscene trigger.
    # Plus it wouldn't really improve anything, given that the Temples are randomized anyway.
    (LevelCRC.MONKEY_TEMPLE, LevelCRC.MONKEY_SPIRIT),
    (LevelCRC.MONKEY_SPIRIT, LevelCRC.MONKEY_TEMPLE),
    (LevelCRC.SCORPION_TEMPLE, LevelCRC.SCORPION_SPIRIT),
    (LevelCRC.SCORPION_SPIRIT, LevelCRC.SCORPION_TEMPLE),
    (LevelCRC.PENGUIN_TEMPLE, LevelCRC.PENGUIN_SPIRIT),
    (LevelCRC.PENGUIN_SPIRIT, LevelCRC.PENGUIN_TEMPLE),
    # The 5 Native Games are currently chosen to not be randomized.
    # If we at some point decide to randomize them anyway we'll have to do some rigorous testing,
    # because it's very much possible this will cause some bugs.
    (LevelCRC.NATIVE_VILLAGE, LevelCRC.WHACK_A_TUCO),
    (LevelCRC.WHACK_A_TUCO, LevelCRC.NATIVE_VILLAGE),
    (LevelCRC.NATIVE_VILLAGE, LevelCRC.TUCO_SHOOT),
    (LevelCRC.TUCO_SHOOT, LevelCRC.NATIVE_VILLAGE),
    (LevelCRC.NATIVE_VILLAGE, LevelCRC.RAFT_BOWLING),
    (LevelCRC.RAFT_BOWLING, LevelCRC.NATIVE_VILLAGE),
    (LevelCRC.NATIVE_VILLAGE, LevelCRC.PICKAXE_RACE),
    (LevelCRC.PICKAXE_RACE, LevelCRC.NATIVE_VILLAGE),
    (LevelCRC.NATIVE_VILLAGE, LevelCRC.KABOOM),
    (LevelCRC.KABOOM, LevelCRC.NATIVE_VILLAGE),
    # The Endgame transitions are not randomized.
    # Currently there are no plans to randomize these transitions.
    (LevelCRC.ST_CLAIRE_DAY, LevelCRC.ST_CLAIRE_NIGHT),
    (LevelCRC.ST_CLAIRE_NIGHT, LevelCRC.ST_CLAIRE_DAY),
    (LevelCRC.GATES_OF_EL_DORADO, LevelCRC.JAGUAR),
    (LevelCRC.JAGUAR, LevelCRC.PUSCA),
    (LevelCRC.PUSCA, LevelCRC.GATES_OF_EL_DORADO),
    # The Unused Beta Volcano Level is not randomized yet,
    # but this can absolutely be randomized later at some point.
    # It will require some special code though.
    (LevelCRC.BETA_VOLCANO, LevelCRC.JUNGLE_CANYON),
    (LevelCRC.BETA_VOLCANO, LevelCRC.PLANE_COCKPIT),
)

if CONFIGS.SKIP_WATER_LEVELS:
    _possible_starting_areas = [a for a in _possible_starting_areas if a not in water_levels]
# Call RNG even if this is unused to not impact randomization of other things for the same seed
starting_area = random.choice(_possible_starting_areas)
if CONFIGS.STARTING_AREA is not None:
    starting_area = CONFIGS.STARTING_AREA

TRANSITION_INFOS_DICT_RANDO = TRANSITION_INFOS_DICT.copy()
ALL_POSSIBLE_TRANSITIONS_RANDO = ALL_POSSIBLE_TRANSITIONS

transitions_map: dict[tuple[int, int], Transition] = {}

link_list: list[tuple[Transition, Transition]] = []
__connections_left: dict[int, int] = {}
"""Used in randomization process to track per Area how many exits aren't connected yet."""

loose_ends: list[Transition] = []
sacred_pairs: list[tuple[int, int]] = []
__current_hub = 0


def increment_index(
    old_index: int,
    max_index: int,
    inc: int,
):
    new_index = old_index + inc
    if new_index >= max_index:
        new_index -= max_index
    elif new_index < 0:
        new_index += max_index
    return new_index


def add_exit(area: Area, ex_id: int):
    ex = Exit(
        ex_id,
        TRANSITION_INFOS_DICT_RANDO[ex_id].name,
        None,
    )
    TRANSITION_INFOS_DICT_RANDO[area.area_id] = Area(
        area.area_id,
        area.name,
        area.default_entrance,
        tuple([x for x in TRANSITION_INFOS_DICT_RANDO[area.area_id].exits] + [ex]),
    )
    global ALL_POSSIBLE_TRANSITIONS_RANDO
    ALL_POSSIBLE_TRANSITIONS_RANDO.append(tuple([area.area_id, ex_id]))


def delete_exit(area: Area, ex: Exit):
    TRANSITION_INFOS_DICT_RANDO[area.area_id] = Area(
        area.area_id,
        area.name,
        area.default_entrance,
        tuple([x for x in TRANSITION_INFOS_DICT_RANDO[area.area_id].exits if x != ex]),
    )
    global ALL_POSSIBLE_TRANSITIONS_RANDO
    ALL_POSSIBLE_TRANSITIONS_RANDO = [
        x for x in ALL_POSSIBLE_TRANSITIONS_RANDO
        if x != tuple([area.area_id, ex.area_id])
    ]


def remove_disabled_exits():
    for area in TRANSITION_INFOS_DICT.values():
        for ex in area.exits:
            current = (area.area_id, ex.area_id)
            if current in one_way_exits or current in disabled_exits:
                delete_exit(area, ex)


def twin_outposts_underwater_prep():
    # create new area: Jungle Outpost (with 1 exit to Flooded Courtyard and 1 exit to Twin Outposts Underwater)
    TRANSITION_INFOS_DICT_RANDO[Outpost.JUNGLE] = Area(
        Outpost.JUNGLE,
        "Jungle Outpost",
        LevelCRC.FLOODED_COURTYARD,
        tuple(),
    )
    area = TRANSITION_INFOS_DICT_RANDO[Outpost.JUNGLE]
    add_exit(area, LevelCRC.FLOODED_COURTYARD)
    add_exit(area, LevelCRC.TWIN_OUTPOSTS_UNDERWATER)
    # create new area: Burning Outpost (with 1 exit to Turtle Monument and 1 exit to Twin Outposts Underwater)
    TRANSITION_INFOS_DICT_RANDO[Outpost.BURNING] = Area(
        Outpost.BURNING,
        "Burning Outpost",
        LevelCRC.TURTLE_MONUMENT,
        tuple(),
    )
    area = TRANSITION_INFOS_DICT_RANDO[Outpost.BURNING]
    add_exit(area, LevelCRC.TURTLE_MONUMENT)
    add_exit(area, LevelCRC.TWIN_OUTPOSTS_UNDERWATER)
    # in area Twin outposts remove all 3 exits (is effectively the same as removing the level entirely)
    area = TRANSITION_INFOS_DICT_RANDO[LevelCRC.TWIN_OUTPOSTS]
    for i in range(3):
        delete_exit(
            TRANSITION_INFOS_DICT_RANDO[LevelCRC.TWIN_OUTPOSTS],
            TRANSITION_INFOS_DICT_RANDO[LevelCRC.TWIN_OUTPOSTS].exits[0],
        )
    # in area flooded courtyard replace exit Twin Outposts with exit Outpost.Jungle
    area = TRANSITION_INFOS_DICT_RANDO[LevelCRC.FLOODED_COURTYARD]
    for ex in area.exits:
        if ex.area_id == LevelCRC.TWIN_OUTPOSTS:
            delete_exit(area, ex)
            break
    add_exit(area, Outpost.JUNGLE)
    # in area turtle monument replace exit Twin Outposts with exit Outpost.Burning
    area = TRANSITION_INFOS_DICT_RANDO[LevelCRC.TURTLE_MONUMENT]
    for ex in area.exits:
        if ex.area_id == LevelCRC.TWIN_OUTPOSTS:
            delete_exit(area, ex)
            break
    add_exit(area, Outpost.BURNING)
    # in area Twin outposts underwater remove the 1 exit it has,
    # and replace them with 1 exit to Outpost.Jungle and 1 to Outpost.Burning
    area = TRANSITION_INFOS_DICT_RANDO[LevelCRC.TWIN_OUTPOSTS_UNDERWATER]
    delete_exit(area, area.exits[0])
    add_exit(area, Outpost.JUNGLE)
    add_exit(area, Outpost.BURNING)


def initialize_connections_left():
    for area in TRANSITION_INFOS_DICT_RANDO.values():
        __connections_left[area.area_id] = len(area.exits)


def calculate_mirror(
    original: Transition,
    redirect: Transition,
):
    mirror_original = Transition(from_=redirect.to, to=redirect.from_)
    mirror_redirect = Transition(from_=original.to, to=original.from_)
    return mirror_original, mirror_redirect


def create_connection(
    origin: Transition,
    redirect: Transition,
):
    global _possible_origins_bucket
    global _possible_redirections_bucket
    global link_list
    global total_con_left
    global loose_ends
    global sacred_pairs

    if len(loose_ends) > 0 and (origin.from_ == __current_hub or redirect.to == __current_hub):
        sacred_pairs.append((origin.from_, redirect.to))

    link_list.append((origin, redirect))
    _possible_origins_bucket.remove(origin)
    _possible_redirections_bucket.remove(redirect)
    if redirect in loose_ends:
        loose_ends.remove(redirect)
        sacred_pairs.append((origin.from_, redirect.to))

    mirror_origin, mirror_redirect = calculate_mirror(origin, redirect)

    link_list.append((mirror_origin, mirror_redirect))
    _possible_origins_bucket.remove(mirror_origin)
    _possible_redirections_bucket.remove(mirror_redirect)
    if mirror_redirect in loose_ends:
        loose_ends.remove(mirror_redirect)
        sacred_pairs.append((origin.from_, redirect.to))

    __connections_left[origin[0]] -= 1
    __connections_left[mirror_origin[0]] -= 1
    total_con_left -= 2


def delete_connection(
    origin: Transition,
    redirect: Transition,
):
    global _possible_origins_bucket
    global _possible_redirections_bucket
    global link_list
    global total_con_left

    link_list.remove((origin, redirect))
    _possible_origins_bucket.append(origin)
    _possible_redirections_bucket.append(redirect)

    mirror_origin, mirror_redirect = calculate_mirror(origin, redirect)

    link_list.remove((mirror_origin, mirror_redirect))
    _possible_origins_bucket.append(mirror_origin)
    _possible_redirections_bucket.append(mirror_redirect)

    __connections_left[origin[0]] += 1
    __connections_left[mirror_origin[0]] += 1
    total_con_left += 2


def choose_random_exit(
    level: int,
    bucket_type: int,
    priority: int,
):
    all_exits_available: list[int] = []
    if bucket_type == BucketType.ORIGIN:
        all_exits_available = [
            trans.to for trans in _possible_origins_bucket
            if trans.from_ == level
        ]
    elif bucket_type == BucketType.REDIRECT:
        all_exits_available = [
            trans.from_ for trans in _possible_redirections_bucket
            if trans.to == level
        ]
    relevant_loose_end_exits = [
        loose_end.from_ for loose_end in loose_ends
        if loose_end.to == level
    ]
    preferred_exits: list[int] = []
    if priority == Priority.CLOSED:
        preferred_exits = relevant_loose_end_exits.copy()
    elif priority == Priority.OPEN:
        preferred_exits = [
            ex for ex in all_exits_available
            if ex not in relevant_loose_end_exits
        ]
    if len(preferred_exits) > 0:
        return random.choice(preferred_exits)
    else:
        return random.choice(all_exits_available)


def connect_two_areas(
    level_from: int,
    level_to: int,
):
    from_exit = choose_random_exit(level_from, BucketType.ORIGIN, Priority.CLOSED)
    to_entrance = choose_random_exit(level_to, BucketType.REDIRECT, Priority.OPEN)

    origin = Transition(level_from, from_exit)
    redirect = Transition(to_entrance, level_to)
    create_connection(origin, redirect)


def connect_to_existing(
    index: int,
    level_list: Sequence[Area],
):
    global __current_hub

    levels_chosen: list[int] = []
    current_con_left = __connections_left[level_list[index].area_id]
    minimum_chosen = 1

    levels_available: list[int] = []
    for i in range(len(level_list)):
        if i == index:
            break
        if __connections_left[level_list[i].area_id] > 0:
            levels_available.append(level_list[i].area_id)

    if len(loose_ends) > 0:
        closed_door_level = random.choice([trans.to for trans in loose_ends])
        levels_chosen.extend([__current_hub, closed_door_level])  # order is important!
        levels_available.remove(closed_door_level)
        levels_available.remove(__current_hub)
        current_con_left -= 2
        minimum_chosen = 0
        if __connections_left[__current_hub] == 1:
            current_con_left -= 1

    amount_chosen = random.randint(minimum_chosen, min(current_con_left, len(levels_available)))
    levels_chosen.extend(random.sample(levels_available, amount_chosen))
    for level_chosen in levels_chosen:
        connect_two_areas(level_chosen, level_list[index].area_id)
    if len(loose_ends) > 0 and __connections_left[__current_hub] == 0:
        __current_hub = level_list[index].area_id

def insert_area_inbetween(
    old_origin: Transition,
    old_redirect: Transition,
    new_level: int,
):
    global sacred_pairs
    pair = tuple([old_origin.from_, old_redirect.to])
    mirror_pair = tuple([old_redirect.to, old_origin.from_])
    if pair in sacred_pairs or mirror_pair in sacred_pairs:
        sacred_pairs = [ x for x in sacred_pairs if x != pair and x != mirror_pair]
        sacred_pairs.extend([
            (new_level, old_origin.from_),
            (new_level, old_redirect.to),
        ])

    delete_connection(old_origin, old_redirect)

    new_redirect_entrance = choose_random_exit(new_level, BucketType.REDIRECT, Priority.OPEN)
    new_redirect = Transition(new_redirect_entrance, new_level)
    create_connection(old_origin, new_redirect)

    new_origin_exit = choose_random_exit(new_level, BucketType.ORIGIN, Priority.OPEN)
    new_origin = Transition(new_level, new_origin_exit)
    create_connection(new_origin, old_redirect)


def remove_area_inbetween(
    area_one: int,
    area_two: int,
    level_to_remove: int,
):
    for link in link_list:
        if link[0].from_ == area_one and link[1].to == level_to_remove:
            delete_connection(link[0], link[1])
            break

    for link in link_list:
        if link[0].from_ == area_two and link[1].to == level_to_remove:
            delete_connection(link[0], link[1])
            break

    connect_two_areas(area_one, area_two)


def can_reach_other_side(
    chosen_link: tuple[Transition, Transition],
    current_links: list[tuple[Transition, Transition]],
):
    unchecked_links = current_links.copy()
    areas_reachable = [chosen_link[0][0]]
    new_area_reached = True
    goal_reached = False
    while new_area_reached and not goal_reached:
        new_area_reached = False
        new_links_reached = [x for x in unchecked_links if x[0][0] in areas_reachable]
        if len(new_links_reached) > 0:
            new_area_reached = True
            for new_link in new_links_reached:
                unchecked_links.remove(new_link)
                if new_link[1][1] == chosen_link[1][1]:
                    goal_reached = True
                    break
                if new_link[1][1] not in areas_reachable:
                    areas_reachable.append(new_link[1][1])
    return goal_reached


def check_part_of_loop(
    chosen_link: tuple[Transition, Transition],
    link_list: list[tuple[Transition, Transition]],
):
    unchecked_links = link_list.copy()
    for closed_door_exit in closed_door_exits:
        for link in unchecked_links:
            if link[1] == closed_door_exit:
                unchecked_links.remove(link)
                break

    pair = tuple([chosen_link[0].from_, chosen_link[1].to])
    mirror_pair = tuple([chosen_link[1].to, chosen_link[0].from_])

    if pair in sacred_pairs or mirror_pair in sacred_pairs:
        return False

    chosen_mirror = calculate_mirror(chosen_link[0], chosen_link[1])

    unchecked_links.remove(chosen_link)
    unchecked_links.remove(chosen_mirror)

    if can_reach_other_side(chosen_link, unchecked_links):
        return can_reach_other_side(chosen_mirror, unchecked_links)
    else:
        return False


def find_and_break_open_connection(link_list: list[tuple[Transition, Transition]]):
    direc = random.choice([-1, 1])
    index = random.randrange(len(link_list))
    valid_link = False
    CRASH_COUNTER = 0
    while not valid_link:
        valid_link = check_part_of_loop(link_list[index], link_list)
        if not valid_link:
            index = increment_index(index, len(link_list), direc)
            CRASH_COUNTER += 1
            if CRASH_COUNTER > 1000:
                raise Exception("NO CONNECTION FOUND")
    delete_connection(link_list[index][0], link_list[index][1])


def remove_water_levels():
    for water_level in water_levels:
        connected_levels: list[int] = []
        for link in link_list:
            if link[0].from_ == water_level:
                connected_levels.append(link[1].to)
        remove_area_inbetween(connected_levels[0], connected_levels[1], water_level)


def get_random_one_way_redirection(original: Transition):
    possible_redirections = [
        redirect for redirect in _possible_redirections_bucket
        if original.from_ != redirect.to  # Prevent looping on itself
    ]
    if len(possible_redirections) > 0:
        return random.choice(possible_redirections)
    return None


def set_transitions_map():  # noqa: PLR0915 # TODO: Break up in smaller functions
    transitions_map.clear()
    remove_disabled_exits()
    twin_outposts_underwater_prep()
    initialize_connections_left()

    if not CONFIGS.SKIP_JAGUAR:
        starting_default = TRANSITION_INFOS_DICT_RANDO[starting_area].default_entrance
        tutorial_original = Transition(from_=LevelCRC.JAGUAR, to=LevelCRC.PLANE_CUTSCENE)
        tutorial_redirect = Transition(from_=starting_default, to=starting_area)
        transitions_map[tutorial_original] = tutorial_redirect

    global _possible_origins_bucket
    global _possible_redirections_bucket
    _possible_origins_bucket = list(starmap(Transition, ALL_POSSIBLE_TRANSITIONS_RANDO))
    _possible_redirections_bucket = _possible_origins_bucket.copy()

    if CONFIGS.LINKED_TRANSITIONS:
        # Ground rules:
        # 1. you can't make a transition from a level to itself
        # 2. any 2 levels may have a maximum of 1 connection between them (as long as it's 2-way)

        closed_door_levels = [trans.to for trans in closed_door_exits]
        closed_door_levels = list(dict.fromkeys(closed_door_levels))  # remove duplicates
        random.shuffle(closed_door_levels)

        level_list = [
            area for area in TRANSITION_INFOS_DICT_RANDO.values()
            if __connections_left[area.area_id] > 0
        ]
        random.shuffle(level_list)
        level_list.sort(key=lambda a: (
            a.area_id in closed_door_levels, __connections_left[a.area_id]
        ), reverse=True)

        global __current_hub
        global loose_ends
        global total_con_left

        __current_hub = closed_door_levels[0]  # this list is shuffled, so just pick the first one
        loose_ends = [*closed_door_exits]
        total_con_left = sum(__connections_left[level] for level in closed_door_levels)

        for index in range(1, len(closed_door_levels)):  # we skip the HUB, so we don't start at 0
            direc = random.choice([-1, 1])
            index_chosen = random.randrange(index)
            valid_level = False
            for loose_end in loose_ends:
                if loose_end.to == __current_hub:
                    index_chosen = 0  # at this stage the HUB will always stay as index 0
                    valid_level = True
                    break
            while not valid_level:
                for loose_end in loose_ends:
                    if loose_end.to == closed_door_levels[index_chosen]:
                        valid_level = True
                        break
                if not valid_level:
                    index_chosen = increment_index(index_chosen, index, direc)
            connect_two_areas(closed_door_levels[index_chosen], closed_door_levels[index])

        index = len(closed_door_levels)  # we skip the closed_door_levels, as they are already done
        while index < len(level_list):
            choice = random.choice(tuple(Choice))

            # Option 1: connect to one or more existing levels
            if total_con_left > 0 and (
                len(loose_ends) > 0
                or __connections_left[level_list[index].area_id] == 1
                or choice == Choice.CONNECT
            ) and not (
                CONFIGS.SKIP_WATER_LEVELS
                and level_list[index].area_id in water_levels
            ):
                total_con_left += __connections_left[level_list[index].area_id]
                connect_to_existing(index, level_list)

            # Option 2: put the current level inbetween an already established connection
            elif __connections_left[level_list[index].area_id] > 1:
                total_con_left += __connections_left[level_list[index].area_id]
                link_chosen = random.choice(link_list)
                insert_area_inbetween(link_chosen[0], link_chosen[1], level_list[index].area_id)

            # Option 3: break open a connection that's part of a loop, then restart iteration
            else:
                try:
                    find_and_break_open_connection(link_list)
                except Exception as e:
                    if str(e) == 'NO CONNECTION FOUND':
                        print('')
                        print('ATTENTION ATTENTION: THE RANDOMIZER CRASHED!!!')
                        print('Please notify a developer!')
                        print('')
                        break
                    else:
                        raise
                continue

            index += 1

        if CONFIGS.SKIP_WATER_LEVELS:
            remove_water_levels()

        # Once the link_list is completed, it's time to fill the transitions_map:
        for link in link_list:
            transitions_map[link[0]] = link[1]

        # the one_way_transitions are added last in order to keep the rest as simple as possible
        one_way_redirects = list(one_way_exits)
        random.shuffle(one_way_redirects)
        for original in one_way_exits:
            if one_way_redirects[0].to == original.from_:
                transitions_map[original] = one_way_redirects.pop(1)
            else:
                transitions_map[original] = one_way_redirects.pop(0)
    else:
        # Ground rules:
        # 1. you can't make a transition from a level to itself
        _possible_redirections_bucket.extend(one_way_exits)
        for area in TRANSITION_INFOS_DICT_RANDO.values():
            for to_og in (exit_.area_id for exit_ in area.exits):
                original = Transition(from_=area.area_id, to=to_og)
                redirect = get_random_one_way_redirection(original)
                if redirect is not None:
                    transitions_map[original] = redirect
                    _possible_redirections_bucket.remove(redirect)
        for original in one_way_exits:
            redirect = get_random_one_way_redirection(original)
            if redirect is not None:
                transitions_map[original] = redirect
                _possible_redirections_bucket.remove(redirect)
