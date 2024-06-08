# https://github.com/Felk/dolphin/tree/scripting-preview2

from __future__ import annotations

import os
import sys
from pathlib import Path

from dolphin import event, memory  # pyright: ignore[reportMissingModuleSource]

dolphin_path = Path().absolute()
print("Dolphin path:", dolphin_path)
real_scripts_path = os.path.realpath(dolphin_path / "Scripts")
print("Real Scripts path:", real_scripts_path)
sys.path.append(f"{real_scripts_path}/Entrance Randomizer")
# Wait for the first frame before scanning the game for constants
await event.frameadvance()  # noqa: F704, PLE1142  # pyright: ignore

import CONFIGS
from lib.constants import *  # noqa: F403
from lib.constants import __version__
from lib.entrance_rando import (
    highjack_transition,
    highjack_transition_rando,
    remove_disabled_exits,
    set_transitions_map,
    starting_area,
    transitions_map,
)
from lib.graph_creation import create_graphml
from lib.shaman_shop import patch_shaman_shop, randomize_shaman_shop
from lib.utils import (
    draw_text,
    dump_spoiler_logs,
    follow_pointer_path,
    prevent_transition_softlocks,
    reset_draw_text_index,
    state,
)

remove_disabled_exits()
set_transitions_map()
randomize_shaman_shop()

# Create .graphml file
create_graphml(transitions_map, seed_string, starting_area)

# This is necessary until/unless I map all areas even those not randomized.
try:
    starting_area_name = TRANSITION_INFOS_DICT[starting_area].name
except KeyError:
    starting_area_name = hex(starting_area).upper() + " (not in randomization)"

# Dump spoiler logs
dump_spoiler_logs(starting_area_name, transitions_map, seed_string)
create_graphml(transitions_map, seed_string, starting_area)


async def main_loop():
    # Read memory, setup loop values, print debug to screen
    reset_draw_text_index()
    state.current_area_old = state.current_area_new
    state.area_load_state_old = state.area_load_state_new
    await event.frameadvance()
    state.current_area_new = memory.read_u32(ADDRESSES.current_area)
    state.area_load_state_new = memory.read_u32(ADDRESSES.area_load_state)
    current_area = TRANSITION_INFOS_DICT.get(state.current_area_new)
    previous_area_id = memory.read_u32(follow_pointer_path(ADDRESSES.prev_area))
    previous_area = TRANSITION_INFOS_DICT.get(previous_area_id)
    draw_text(f"Rando version: {__version__}")
    draw_text(f"Seed: {seed_string}")
    draw_text(patch_shaman_shop())
    draw_text(
        "Starting area: " + (
            f"{hex(starting_area).upper()} (Random)"
            if CONFIGS.STARTING_AREA is None
            else starting_area_name
        ),
    )
    draw_text(
        f"Current area: {hex(state.current_area_new).upper()} "
        + (f"({current_area.name})" if current_area else ""),
    )
    draw_text(
        f"From entrance: {hex(previous_area_id).upper()} "
        + (f"({previous_area.name})" if previous_area else ""),
    )

    # Always re-enable Item Swap.
    if memory.read_u32(ADDRESSES.item_swap) == 1:
        memory.write_u32(ADDRESSES.item_swap, 0)

    # Skip both Jaguar fights if noted in CONFIGS
    if CONFIGS.SKIP_JAGUAR:
        if highjack_transition(LevelCRC.MAIN_MENU, LevelCRC.JAGUAR, starting_area):
            return
        if highjack_transition(LevelCRC.GATES_OF_EL_DORADO, LevelCRC.JAGUAR, LevelCRC.PUSCA):
            return

    # Standardize the Altar of Ages exit to remove the Altar -> BBCamp transition
    if highjack_transition(
            LevelCRC.ALTAR_OF_AGES,
            LevelCRC.BITTENBINDERS_CAMP,
            LevelCRC.MYSTERIOUS_TEMPLE,
    ):
        state.current_area_new = LevelCRC.MYSTERIOUS_TEMPLE
        # Even if the cutscene isn't actually watched.
        # Just leaving the Altar is good enough for the rando.
        state.visited_altar_of_ages = True

    # Standardize the Viracocha Monoliths cutscene
    if highjack_transition(
            None,
            LevelCRC.VIRACOCHA_MONOLITHS_CUTSCENE,
            LevelCRC.VIRACOCHA_MONOLITHS,
    ):
        state.current_area_new = LevelCRC.VIRACOCHA_MONOLITHS

    # Standardize St. Claire's Excavation Camp
    if highjack_transition(None, LevelCRC.ST_CLAIRE_NIGHT, LevelCRC.ST_CLAIRE_DAY):
        state.current_area_new = LevelCRC.ST_CLAIRE_DAY

    # TODO: Skip swim levels (3)

    redirect = highjack_transition_rando()
    if redirect:
        state.current_area_new = redirect[1]

    prevent_transition_softlocks()


while True:
    await main_loop()  # noqa: F704, PLE1142  # pyright: ignore
