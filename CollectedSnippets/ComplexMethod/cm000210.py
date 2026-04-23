def do_something(back_pointer, goal, start):
    grid = np.char.chararray((n, n))
    for i in range(n):
        for j in range(n):
            grid[i][j] = "*"

    for i in range(n):
        for j in range(n):
            if (j, (n - 1) - i) in blocks:
                grid[i][j] = "#"

    grid[0][(n - 1)] = "-"
    x = back_pointer[goal]
    while x != start:
        (x_c, y_c) = x
        # print(x)
        grid[(n - 1) - y_c][x_c] = "-"
        x = back_pointer[x]
    grid[(n - 1)][0] = "-"

    for i in range(n):
        for j in range(n):
            if (i, j) == (0, n - 1):
                print(grid[i][j], end=" ")
                print("<-- End position", end=" ")
            else:
                print(grid[i][j], end=" ")
        print()
    print("^")
    print("Start position")
    print()
    print("# is an obstacle")
    print("- is the path taken by algorithm")
    print("PATH TAKEN BY THE ALGORITHM IS:-")
    x = back_pointer[goal]
    while x != start:
        print(x, end=" ")
        x = back_pointer[x]
    print(x)
    sys.exit()