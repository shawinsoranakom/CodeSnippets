def solve_all(grids, name="", showif=0.0):

    def time_solve(grid):
        start = time.monotonic()
        values = solve(grid)
        t = time.monotonic() - start
        if showif is not None and t > showif:
            display(grid_values(grid))
            if values:
                display(values)
            print(f"({t:.5f} seconds)\n")
        return (t, solved(values))

    times, results = zip(*[time_solve(grid) for grid in grids])
    if (n := len(grids)) > 1:
        print(
            "Solved %d of %d %s puzzles (avg %.2f secs (%d Hz), max %.2f secs)."  
            % (sum(results), n, name, sum(times) / n, n / sum(times), max(times))
        )
