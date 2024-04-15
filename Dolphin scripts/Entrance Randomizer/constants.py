from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from itertools import chain

from dolphin import memory  # pyright: ignore[reportMissingModuleSource]
from transition_infos import transition_infos


class ShopPriceOffset(IntEnum):
    ExtraHealth1 = 4
    ExtraHealth2 = 8
    ExtraHealth3 = 12
    ExtraHealth4 = 16
    ExtraHealth5 = 20
    Canteen1 = 92
    Canteen2 = 96
    Canteen3 = 100
    Canteen4 = 104
    Canteen5 = 108
    SmashStrike = 36
    SuperSling = 44
    Breakdance = 28
    JungleNotes = 60
    NativeNotes = 52
    CavernNotes = 68
    MountainNotes = 76
    MysteryItem = 84


class ShopCountOffset(IntEnum):
    ExtraHealth = ShopPriceOffset.ExtraHealth1 - 4
    Canteen = ShopPriceOffset.Canteen1 - 4
    SmashStrike = ShopPriceOffset.SmashStrike - 4
    SuperSling = ShopPriceOffset.SuperSling - 4
    Breakdance = ShopPriceOffset.Breakdance - 4
    JungleNotes = ShopPriceOffset.JungleNotes - 4
    NativeNotes = ShopPriceOffset.NativeNotes - 4
    CavernNotes = ShopPriceOffset.CavernNotes - 4
    MountainNotes = ShopPriceOffset.MountainNotes - 4
    MysteryItem = ShopPriceOffset.MysteryItem - 4


@dataclass
class Addresses:
    version_string: str
    prev_area: list[int]
    current_area: int
    item_swap: int
    shaman_shop_struct: int


MAX_IDOLS = 138
DEFAULT_SHOP_PRICES = [2, 4, 8, 16, 32, 1, 2, 3, 4, 5, 10, 10, 10, 9, 7, 7, 8, 0]
MAPLESS_SHOP_PRICES = [0x04, 8, 16, 32, 0x00003, 4, 5, 10, 10, 10, 9, 7, 7, 8]
"""Same as `DEFAULT_SHOP_PRICES` but with 4 lowest prices removed."""

DRAW_TEXT_STEP = 24
DRAW_TEXT_OFFSET_X = 272

TRANSITION_INFOS_DICT = {
    area.area_id: area for area in chain(*transition_infos)
}
ALL_TRANSITION_AREAS = {area.area_id for area in chain(*transition_infos)}
ALL_POSSIBLE_EXITS = [
    exit_.area_id for exit_ in chain(
        *(area.exits for area in TRANSITION_INFOS_DICT.values()),
    )
]

_game_id_base = "".join([
    chr(memory.read_u8(0x80000000 + i))
    for i in range(3)
])
GAME_REGION = chr(memory.read_u8(0x80000003))
_developer_id = "".join([
    chr(memory.read_u8(0x80000004 + i))
    for i in range(2)
])
GAME_VERSION = memory.read_u8(0x80000007)
IS_GC = _game_id_base == "GPH"
IS_WII = _game_id_base == "RPF"

TODO = 0x0

# Including the version number seems overkill, I don't think there was ever a non v0. Can add later if needed.
if GAME_VERSION != 0:
    raise Exception(f"Unknown game version {GAME_VERSION}!")
_addresses_map = {
    "GPH": {
        "D": Addresses("GC DE 0-00", [0x80747648], 0x80417F50, 0x804C7734, TODO),
        "E": Addresses("GC US 0-00", [0x8072B648], 0x8041BEB4, 0x804CB694, 0x7E00955C),
        "F": Addresses("GC FR 0-00", [0x80747648], 0x80417F30, 0x804C7714, TODO),
        "P": Addresses("GC EU 0-00", [0x80747648], 0x80417F10, 0x804C76F4, TODO),
    },
    "RPF": {
        "E": Addresses("Wii US 0-00", [0x804542DC, 0x8], 0x80448D04, 0x80446608, TODO),
        "P": Addresses("Wii EU 0-00", [0x804546DC, 0x18], 0x80449104, 0x80446A08, TODO),
    },
}

_addresses = _addresses_map.get(_game_id_base, {}).get(GAME_REGION)
if not _addresses or _developer_id != "52":
    raise Exception(
        "Unknown version of Pitfall The Lost Expedition "
        + f"(game id -> {_game_id_base}{GAME_REGION}{_developer_id}, version -> {GAME_VERSION})",
    )

ADDRESSES = _addresses
print(f"Detected {ADDRESSES.version_string} version!")

# Level CRCs
JAGUAR = 0x99885996
CRASH_SITE = 0xEE8F6900
PLANE_COCKPIT = 0x4A3E4058
CHAMELEON_TEMPLE = 0x0081082C
JUNGLE_CANYON = 0xDEDA69BC
MAMA_OULLO_TOWER = 0x07ECCC35
VIRACOCHA_MONOLITHS = 0x6F498BBD
VIRACOCHA_MONOLITHS_CUTSCENE = 0xE8362F5F
ALTAR_OF_AGES = 0xABD7CCD8
BITTENBINDERS_CAMP = 0x0EF63551
MYSTERIOUS_TEMPLE = 0x099BF148
APU_ILLAPU_SHRINE = 0x5511C46C
SCORPION_TEMPLE = 0x4B08BBEB
ST_CLAIRE_NIGHT = 0x72AD42FA
ST_CLAIRE_DAY = 0x72AD42FA
TELEPORTERS = 0xE97CB47C

GC_MIN_ADDRESS = 0x80000000
GC_MEM_SIZE = 0x1800000
GC_MAX_ADDRESS = 0x80000000 + GC_MEM_SIZE - 1  # so 0x817FFFFF
