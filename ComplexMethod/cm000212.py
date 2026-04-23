def make_common_ground():
    some_list = []
    for x in range(1, 5):
        for y in range(1, 6):
            some_list.append((x, y))

    for x in range(15, 20):
        some_list.append((x, 17))

    for x in range(10, 19):
        for y in range(1, 15):
            some_list.append((x, y))

    # L block
    for x in range(1, 4):
        for y in range(12, 19):
            some_list.append((x, y))
    for x in range(3, 13):
        for y in range(16, 19):
            some_list.append((x, y))
    return some_list