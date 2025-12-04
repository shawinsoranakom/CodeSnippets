def visualise(wt: WaTor, iter_number: int, *, colour: bool = True) -> None:
    
    if colour:
        __import__("os").system("")
        print("\x1b[0;0H\x1b[2J\x1b[?25l")

    reprint = "\x1b[0;0H" if colour else ""
    ansi_colour_end = "\x1b[0m " if colour else " "

    planet = wt.planet
    output = ""

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
    sleep(0.05)
