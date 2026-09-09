"""
Every playable legend and the two weapons it can use, from the game's own HeroTypes data.

A legend can only use its own two weapons, so this is what decides which weapon a fighter may
be given. 

File auto-generated with brawlgym-core/dump_legends on 9/8/2026 at 10:22 PM.
"""
from typing import Dict, List, Tuple

# HeroID -> (name, display name, weapon 1, weapon 2)
LEGENDS: Dict[int, Tuple[str, str, str, str]] = {
    3   : ('Viking'             , 'Bödvar'              , 'Hammer'          , 'Sword'),
    4   : ('Cowgirl'            , 'Cassidy'             , 'Pistol'          , 'Hammer'),
    5   : ('Valkyrie'           , 'Orion'               , 'RocketLance'     , 'Spear'),
    6   : ('Alien'              , 'Lord Vraxx'          , 'RocketLance'     , 'Pistol'),
    7   : ('Caveman'            , 'Gnash'               , 'Hammer'          , 'Spear'),
    8   : ('Witch'              , 'Queen Nai'           , 'Spear'           , 'Katar'),
    9   : ('Highwayman'         , 'Lucien'              , 'Katar'           , 'Pistol'),
    10  : ('Ninja'              , 'Hattori'             , 'Sword'           , 'Spear'),
    11  : ('Knight'             , 'Sir Roland'          , 'RocketLance'     , 'Sword'),
    12  : ('Steampunk'          , 'Scarlet'             , 'Hammer'          , 'RocketLance'),
    13  : ('Thatch'             , 'Thatch'              , 'Sword'           , 'Pistol'),
    14  : ('Cyber'              , 'Ada'                 , 'Pistol'          , 'Spear'),
    15  : ('Super'              , 'Sentinel'            , 'Hammer'          , 'Katar'),
    16  : ('Minotaur'           , 'Teros'               , 'Axe'             , 'Hammer'),
    17  : ('Sentai'             , 'Red Raptor'          , 'Boots'           , 'Orb'),
    18  : ('Elf'                , 'Ember'               , 'Bow'             , 'Katar'),
    19  : ('ActualValk'         , 'Brynn'               , 'Axe'             , 'Spear'),
    20  : ('Cat'                , 'Asuri'               , 'Katar'           , 'Sword'),
    21  : ('Apoc'               , 'Barraza'             , 'Axe'             , 'Pistol'),
    22  : ('Dwarf'              , 'Ulgrim'              , 'Axe'             , 'RocketLance'),
    23  : ('Skeleton'           , 'Azoth'               , 'Bow'             , 'Axe'),
    24  : ('Samurai'            , 'Koji'                , 'Bow'             , 'Sword'),
    25  : ('Marksman'           , 'Diana'               , 'Bow'             , 'Pistol'),
    26  : ('Barbarian'          , 'Jhala'               , 'Axe'             , 'Sword'),
    27  : ('Loki'               , 'Loki'                , 'Katar'           , 'Scythe'),
    28  : ('Golem'              , 'Kor'                 , 'Fists'           , 'Hammer'),
    29  : ('Monk'               , 'Wu Shang'            , 'Fists'           , 'Spear'),
    30  : ('TechnoNinja'        , 'Val'                 , 'Fists'           , 'Sword'),
    31  : ('Dragon'             , 'Ragnir'              , 'Katar'           , 'Axe'),
    32  : ('Mobster'            , 'Cross'               , 'Pistol'          , 'Fists'),
    33  : ('Egyptian'           , 'Mirage'              , 'Scythe'          , 'Spear'),
    34  : ('Reaper'             , 'Nix'                 , 'Scythe'          , 'Pistol'),
    35  : ('Werewolf'           , 'Mordex'              , 'Scythe'          , 'Fists'),
    36  : ('Ninetails'          , 'Yumiko'              , 'Bow'             , 'Hammer'),
    37  : ('Spacehunter'        , 'Artemis'             , 'RocketLance'     , 'Scythe'),
    38  : ('Thief'              , 'Caspian'             , 'Fists'           , 'Katar'),
    39  : ('Corsair'            , 'Sidra'               , 'Cannon'          , 'Sword'),
    40  : ('Brute'              , 'Xull'                , 'Cannon'          , 'Axe'),
    41  : ('Soldier'            , 'Isaiah'              , 'Cannon'          , 'Pistol'),
    42  : ('Inuit'              , 'Kaya'                , 'Spear'           , 'Bow'),
    43  : ('Shinobi'            , 'Jiro'                , 'Sword'           , 'Scythe'),
    44  : ('Wuxia'              , 'Lin Fei'             , 'Katar'           , 'Cannon'),
    45  : ('Celestial'          , 'Zariel'              , 'Fists'           , 'Bow'),
    46  : ('Rayman'             , 'Rayman'              , 'Fists'           , 'Axe'),
    47  : ('Elfwar'             , 'Dusk'                , 'Spear'           , 'Orb'),
    48  : ('Spellwitch'         , 'Fait'                , 'Scythe'          , 'Orb'),
    49  : ('Thor'               , 'Thor'                , 'Hammer'          , 'Orb'),
    50  : ('RageFighter'        , 'Petra'               , 'Fists'           , 'Orb'),
    54  : ('Sellsword'          , 'Jaeyun'              , 'Sword'           , 'Greatsword'),
    55  : ('ActualShark'        , 'Mako'                , 'Katar'           , 'Greatsword'),
    56  : ('GhostArmor'         , 'Magyar'              , 'Hammer'          , 'Greatsword'),
    57  : ('BountyHunter'       , 'Reno'                , 'Pistol'          , 'Orb'),
    58  : ('BirdBard'           , 'Munin'               , 'Bow'             , 'Scythe'),
    60  : ('Ezio'               , 'Ezio'                , 'Sword'           , 'Orb'),
    61  : ('Roboengineer'       , 'Seven'               , 'Spear'           , 'Cannon'),
    62  : ('GreekSpeedster'     , 'Thea'                , 'Boots'           , 'RocketLance'),
    63  : ('Luchador'           , 'Tezca'               , 'Boots'           , 'Fists'),
    64  : ('Assassin'           , 'Vivi'                , 'Boots'           , 'Pistol'),
    65  : ('Imugi'              , 'Imugi'               , 'Axe'             , 'Greatsword'),
    66  : ('AfricanKing'        , 'King Zuva'           , 'Hammer'          , 'Boots'),
    67  : ('BladeDancer'        , 'Priya'               , 'Chakram'         , 'Sword'),
    68  : ('CyberVirus'         , 'Ransom'              , 'Chakram'         , 'Bow'),
    69  : ('Cleric'             , 'Lady Vera'           , 'Chakram'         , 'Scythe'),
    70  : ('DarkheartMonster'   , 'Rupture'             , 'Katar'           , 'RocketLance'),
    71  : ('ActualGladiator'    , 'Aurus'               , 'Chakram'         , 'Spear'),
    72  : ('AstroGirl'          , 'Qinghua & Baobao'    , 'Orb'             , 'Cannon'),
}

# stable order for one-hot encoding a fighter's legend
LEGEND_IDS: List[int] = sorted(LEGENDS)
LEGEND_INDEX: Dict[int, int] = {hid: i for i, hid in enumerate(LEGEND_IDS)}
# the game reports a fighter's legend by HeroName, which is what maps back to the rest of this table
LEGEND_BY_NAME: Dict[str, int] = {row[0]: hid for hid, row in LEGENDS.items()}


def hero_id_for(hero_name: str) -> int:
    """
    HeroID for a HeroName as the game reports it ("Viking"), or -1 if unknown.
    """
    return LEGEND_BY_NAME.get(hero_name, -1)


def legend_weapons(hero_id: int) -> Tuple[str, ...]:
    """
    The two weapons that legend can use, or () for an unknown id.
    """
    row = LEGENDS.get(int(hero_id))
    return (row[2], row[3]) if row else ()


def legend_name(hero_id: int) -> str:
    """
    The legend's display name, or "" for an unknown id.
    """
    row = LEGENDS.get(int(hero_id))
    return row[1] if row else ""
