def visualise(wt: WaTor, iter_number: int, *, colour: bool = True) -> None:
    """
    Visually displays the Wa-Tor planet using
    an ascii code in terminal to clear and re-print
    the Wa-Tor planet at intervals.

    Uses ascii colour codes to colourfully display the predators and prey:
        * (0x60f197) Prey = ``#``
        * (0xfffff) Predator = ``x``

    >>> wt = WaTor(30, 30)
    >>> wt.set_planet([
    ... [Entity(True, coords=(0, 0)), Entity(False, coords=(0, 1)), None],
    ... [Entity(False, coords=(1, 0)), None, Entity(False, coords=(1, 2))],
    ... [None, Entity(True, coords=(2, 1)), None]
    ... ])
    >>> visualise(wt, 0, colour=False)  # doctest: +NORMALIZE_WHITESPACE
    #  x  .
    x  .  x
    .  #  .
    <BLANKLINE>
    Iteration: 0 | Prey count: 2 | Predator count: 3 |
    """
    if colour:
        __import__("os").system("")
        print("\x1b[0;0H\x1b[2J\x1b[?25l")

    reprint = "\x1b[0;0H" if colour else ""
    ansi_colour_end = "\x1b[0m " if colour else " "

    planet = wt.planet
    output = ""

    # Iterate over every entity in the planet
    for row in planet:
        for entity in row:
            if entity is None:
                output += " . "
            else:
                if colour is True:
                    output += (
                        "\x1b[38;2;96;241;151m"
                        if entity.prey
                        else "\x1b[38;2;255;255;15m"
                    )
                output += f" {'#' if entity.prey else 'x'}{ansi_colour_end}"

        output += "\n"

    entities = wt.get_entities()
    prey_count = sum(entity.prey for entity in entities)

    print(
        f"{output}\n Iteration: {iter_number} | Prey count: {prey_count} | "
        f"Predator count: {len(entities) - prey_count} | {reprint}"
    )
    # Block the thread to be able to visualise seeing the algorithm
    sleep(0.05)