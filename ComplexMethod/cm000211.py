def expand_state(
    s,
    j,
    visited,
    g_function,
    close_list_anchor,
    close_list_inad,
    open_list,
    back_pointer,
):
    for itera in range(n_heuristic):
        open_list[itera].remove_element(s)
    # print("s", s)
    # print("j", j)
    (x, y) = s
    left = (x - 1, y)
    right = (x + 1, y)
    up = (x, y + 1)
    down = (x, y - 1)

    for neighbours in [left, right, up, down]:
        if neighbours not in blocks:
            if valid(neighbours) and neighbours not in visited:
                # print("neighbour", neighbours)
                visited.add(neighbours)
                back_pointer[neighbours] = -1
                g_function[neighbours] = float("inf")

            if valid(neighbours) and g_function[neighbours] > g_function[s] + 1:
                g_function[neighbours] = g_function[s] + 1
                back_pointer[neighbours] = s
                if neighbours not in close_list_anchor:
                    open_list[0].put(neighbours, key(neighbours, 0, goal, g_function))
                    if neighbours not in close_list_inad:
                        for var in range(1, n_heuristic):
                            if key(neighbours, var, goal, g_function) <= W2 * key(
                                neighbours, 0, goal, g_function
                            ):
                                open_list[j].put(
                                    neighbours, key(neighbours, var, goal, g_function)
                                )