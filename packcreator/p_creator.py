import random
import pickle


def generatepack_c1c2_special(sheet_index=0, sheet_index_func=lambda a: random.randint(0, 121), setJSON=None):
    """
    Takes a JSON dict object, parsed in the V2 format.

    Returns a pack in the btts.py format, [ ('collector_number','set_code'), ... ].

    Returns indexes of the list which indicate foiled cards.
    """
    distribution = random.choices(
        [d[0] for d in setJSON["distributions_odds"]],
        [d[1] for d in setJSON["distributions_odds"]],
    )[0]
    ABCD_c = random.choices(
        [c[0] for c in setJSON["ABCD_commons_odds"]],
        [c[1] for c in setJSON["ABCD_commons_odds"]],
    )[0]
    ABCD_u = random.choices(
        [u[0] for u in setJSON["ABCD_uncommon_odds"]],
        [u[1] for u in setJSON["ABCD_uncommon_odds"]],
    )[0]
    ABCD_r = random.choices(
        [u[0] for u in setJSON["rare_slot_odds"]],
        [u[1] for u in setJSON["rare_slot_odds"]],
    )[0]
    pack = []  # The pack object. Put [cn,set_code] objects into this list.
    keydrops_c = []
    # Contains the keys from the common ABCD to skip adding to make room for foils.
    keydrops_u = []
    # Contains the keys from the uncommon ABCD to skip adding to make room for foils.
    keydrops_r = 0  # Might be redundant. Tallies the number of rares to drop if using extra sheets. Number rather than list due to rarity independence.
    if "drops" in distribution.keys():
        # Calculate drops, which remove one number from a given key for the ABCD.
        if "c" in distribution["drops"]:
            for d in range(distribution["drops"]["c"]):
                keydrops_c.append(random.choice(list(ABCD_c.keys())))
        if "u" in distribution["drops"]:
            for d in range(distribution["drops"]["u"]):
                keydrops_u.append(random.choice(list(ABCD_u.keys())))
        if "r" in distribution["drops"]:
            keydrops_r += distribution["drops"]["r"]
    for key, value in ABCD_c.items():
        # For each sheet key in the ABCD, take the value and grab that many cards from the sheet.
        sheet_index = sheet_index_func(value)
        for p in range(value - len([j for j in keydrops_c if j == key])):
            pack = pack + [
                (
                    setJSON["ABCD_common_sheets"][key][(sheet_index + p) % len(setJSON["ABCD_common_sheets"][key])],
                    setJSON["set_code"],
                )
            ]
    for key, value in ABCD_u.items():
        # For each sheet key in the ABCD, take the value and grab that many cards from the sheet.
        sheet_index = sheet_index_func(value)
        for p in range(value - len([j for j in keydrops_u if j == key])):
            pack = pack + [
                (
                    setJSON["ABCD_uncommon_sheets"][key][(sheet_index + p) % len(setJSON["ABCD_uncommon_sheets"][key])],
                    setJSON["set_code"],
                )
            ]
    for key, value in ABCD_r.items():
        # Grab that many rares from the selected rare sheet.
        sheet_index = sheet_index_func(value)
        # Manually check if the rare has been hit recently.
        # If it tries to hit a duplicate more than 10 times, reset the tracker. Can't calculate how far out this would be, but it should prevent a ton of duplicate rares.
        # This might introduce some real lag.
        # Also, whiffs on double rares; if taking more than one rare, it could choose X-1 as the pointer and take the duplicate. Not too likely, but possible.

        try:
            with open("prevrares.pickle", "rb") as f:
                prev_rares = pickle.load(f)
        except:
            with open("prevrares.pickle", "wb") as f:
                prev_rares = [[], 0]
                pickle.dump(prev_rares, f)
        while sheet_index in prev_rares[0]:
            # Loop while the rare chosen had been chosen recently. Pick a new one unless the "recent" rares aren't recent anymore.
            prev_rares[1] += 1
            if prev_rares[1] > 50:
                prev_rares = [[], 0]
                break
            else:
                sheet_index = sheet_index_func(value)
        prev_rares[0] += [sheet_index]
        with open("prevrares.pickle", "wb") as f:
            pickle.dump(prev_rares, f)

        # Now that the number has been checked, actually put in the rare.
        for p in range(value - keydrops_r):
            pack = pack + [
                (
                    setJSON["rare_slot_sheets"][key][(sheet_index + value) % len(setJSON["rare_slot_sheets"][key])],
                    setJSON["set_code"],
                )
            ]
    f_indexes = []
    # Tracks the indexes of foils within the pack.
    if "f" in distribution.keys():
        # Grab that many foils from the foil sheets. In the case of multiple foils, rarity is independently selected.
        sheet_index = sheet_index_func(distribution["f"])
        for _ in range(distribution["f"]):
            pack = pack + [
                (
                    (
                        sheet := (
                            random.choices(
                                [g[0] for g in setJSON["foil_sheets_odds"]],
                                [g[1] for g in setJSON["foil_sheets_odds"]],
                            )[0]
                        )
                    )[sheet_index % len(sheet)],
                    setJSON["set_code"],
                )
            ]
            f_indexes.append(len(pack))
    for key in [key for key in distribution.keys() if key not in ["c", "u", "r", "f", "drops"]]:
        # Catch special sheets.
        sheet_index = sheet_index_func(distribution[key])
        for n in range(distribution[key]):
            pack = pack + [
                (
                    (
                        sheet := (
                            random.choices(
                                setJSON["extras_sheets_odds"][key][0],
                                setJSON["extras_sheets_odds"][key][1],
                            )[0]
                        )
                    )[sheet_index % len(sheet)],
                    setJSON["extras_sheets_odds"][key][2],
                )
            ]
    # Reverse the pack and pivot the foil indexes. This hides the rare at the bottom of the card stack in TTS.
    return pack[::-1], [(r + (len(pack) - r) * 2) % len(pack) for r in f_indexes]


def pack_gen_v3(
    set=None,
    func=lambda l_s, c_t: random.randint(0, l_s),
    d_c: dict[str, float] = {},
    seed: int = None,
):
    """
    Takes a JSON dict object, parsed in the V3 format.

    Takes a function with inputs length_of_sheet, count_taken which returns an index within the range of length_of_sheet. Use count_taken for slight duplicate control.

    Takes a duplicate_control list of lists of indexes for choosing rarity controlled cards.

    Returns a pack in the btts.py format, [ ('collector_number','set_code'), ... ].

    Returns indexes of the list which indicate foiled cards.
    """
    if seed is not None:
        random.seed(seed)
    else:
        random.seed(seed := random.randint(0, 2000000))
    pack: list[list[str, str]] = []
    foil_indexes: list[int] = []
    # Choose a distro based on distro[freq]
    distro: dict = random.choices(set["distros"], [s["freq"] for s in set["distros"]], k=1)[0]
    s = None
    if "replace_foil" in set["flag_data"].keys():
        s = None
        sh_key = None
        f_count = 0
        if random.random() < set["flag_data"]["reaplace_foil"]["freq"]:
            s = random.choices(
                [z for z in set["flag_data"]["reaplace_foil"]["slots"].keys()],
                [a for a in set["flag_data"]["reaplace_foil"]["slots"].values()],
                k=1,
            )
            f_count = set["flag_data"]["foil"]["count"]
    # For each slot key in the distro['slots'].keys()
    for slot_key in distro["slots"].keys():
        # Choose a slot[option] based on option[freq]
        struct: dict = random.choices(
            [o["struct"] for o in set["slots"][slot_key]["options"]],
            [o["freq"] for o in set["slots"][slot_key]["options"]],
            k=1,
        )[0]
        # If this slot needs to drop a card from one of its sheets
        drop_choice: dict = {}
        if "drops" in distro.keys():
            if slot_key in distro["drops"].keys():
                drop_choice = random.choices(
                    [o for o in distro["drops"][slot_key]], [o["freq"] for o in distro["drops"][slot_key]], k=1
                )[0]
        # If this slot was chosen to have cards replaced with foil
        if "reaplace_foil" in set["flag_data"].keys():
            if s == slot_key:
                sh_key = random.choice([k for k in struct.keys()])
        # For each key in slot[option]['struct']
        for sheet_key, sheet_take in struct.items():
            # If "duplicate_control" in slot['flags'], pop number from d_c
            # Otherwise, generate starting number using func
            index: int = (
                d_c[slot_key].pop()
                if "duplicate_control" in set["slots"][slot_key]["flags"]
                else func(
                    l_s=len(set["slots"][slot_key]["sheets"][sheet_key]),
                    c_t=struct[sheet_key],
                )
            )
            # If this exact sheet was the one chosen to drop a card
            drop_sheet: int = 0
            if drop_choice != {}:
                if sheet_key == drop_choice["key"]:
                    drop_sheet = drop_choice["count"]
            # For x in range(value)
            # print(slot_key, sheet_key, sheet_take, drop_sheet)
            for c in range(sheet_take - drop_sheet):
                # Take a card from slot['sheets'][key] according to the number plus x
                pack += [
                    set["slots"][slot_key]["sheets"][sheet_key][
                        (index + c) % len(set["slots"][slot_key]["sheets"][sheet_key])
                    ][:]
                ]
                # If "foil" in slot['flags'], add that index to the foil array
                if "foil" in set["slots"][slot_key]["flags"]:
                    foil_indexes.append(len(pack))
            # If this sheet was chosen to have cards replaced by foils
            if "reaplace_foil" in set["flag_data"].keys():
                if s == slot_key:
                    if sh_key == sheet_key:
                        for q in range(f_count):
                            foil_indexes.append(len(pack) - q)
    for i in range(len(pack)):
        if type(pack[i]) is not list:
            pack[i] = [pack[i], set["default_set"]]
    # Return the pack in reverse, return the foil array pivoted around the center
    return (
        pack[::-1],
        [(radix + (len(pack) - radix) * 2) % len(pack) for radix in foil_indexes],
        seed,
    )


if __name__ == "__main__":
    import json
    import point_slicer

    with open("packcreator/sj3/afr_2.json", "rb") as f:
        ooo = json.load(f)
        d_c = {}
        if "flag_data" in ooo.keys():
            if "duplicate_control" in ooo["flag_data"].keys():
                d_c = {
                    k: point_slicer.get_sampled_numbers(
                        24,
                        ooo["flag_data"]["duplicate_control"]["slots_counts"][k]["max_length"]
                        * ooo["flag_data"]["duplicate_control"]["slots_counts"][k]["count"],
                    )
                    for k in ooo["flag_data"]["duplicate_control"]["slots_counts"].keys()
                }
                print(d_c)
        for n in range(24):
            w, n, s = pack_gen_v3(set=ooo, d_c=d_c)
            print(len(w), n, s)
