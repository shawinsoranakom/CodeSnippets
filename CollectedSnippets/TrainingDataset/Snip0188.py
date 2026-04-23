def __judge_point(pt: bool, neighbours: list[list[bool]]) -> bool:
    dead = 0
    alive = 0
    for i in neighbours:
        for status in i:
            if status:
                alive += 1
            else:
                dead += 1

    if pt:
        alive -= 1
    else:
        dead -= 1

    state = pt
    if pt:
        if alive < 2:
            state = False
        elif alive in {2, 3}:
            state = True
        elif alive > 3:
            state = False
    elif alive == 3:
        state = True

    return state
