def multi_a_star(start: TPos, goal: TPos, n_heuristic: int):
    g_function = {start: 0, goal: float("inf")}
    back_pointer = {start: -1, goal: -1}
    open_list = []
    visited = set()

    for i in range(n_heuristic):
        open_list.append(PriorityQueue())
        open_list[i].put(start, key(start, i, goal, g_function))

    close_list_anchor: list[int] = []
    close_list_inad: list[int] = []
    while open_list[0].minkey() < float("inf"):
        for i in range(1, n_heuristic):
            # print(open_list[0].minkey(), open_list[i].minkey())
            if open_list[i].minkey() <= W2 * open_list[0].minkey():
                global t
                t += 1
                if g_function[goal] <= open_list[i].minkey():
                    if g_function[goal] < float("inf"):
                        do_something(back_pointer, goal, start)
                else:
                    _, get_s = open_list[i].top_show()
                    visited.add(get_s)
                    expand_state(
                        get_s,
                        i,
                        visited,
                        g_function,
                        close_list_anchor,
                        close_list_inad,
                        open_list,
                        back_pointer,
                    )
                    close_list_inad.append(get_s)
            elif g_function[goal] <= open_list[0].minkey():
                if g_function[goal] < float("inf"):
                    do_something(back_pointer, goal, start)
            else:
                get_s = open_list[0].top_show()
                visited.add(get_s)
                expand_state(
                    get_s,
                    0,
                    visited,
                    g_function,
                    close_list_anchor,
                    close_list_inad,
                    open_list,
                    back_pointer,
                )
                close_list_anchor.append(get_s)
    print("No path found to goal")
    print()
    for i in range(n - 1, -1, -1):
        for j in range(n):
            if (j, i) in blocks:
                print("#", end=" ")
            elif (j, i) in back_pointer:
                if (j, i) == (n - 1, n - 1):
                    print("*", end=" ")
                else:
                    print("-", end=" ")
            else:
                print("*", end=" ")
            if (j, i) == (n - 1, n - 1):
                print("<-- End position", end=" ")
        print()
    print("^")
    print("Start position")
    print()
    print("# is an obstacle")
    print("- is the path taken by algorithm")