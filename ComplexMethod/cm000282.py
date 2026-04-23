def hill_climbing(
    search_prob,
    find_max: bool = True,
    max_x: float = math.inf,
    min_x: float = -math.inf,
    max_y: float = math.inf,
    min_y: float = -math.inf,
    visualization: bool = False,
    max_iter: int = 10000,
) -> SearchProblem:
    """
    Implementation of the hill climbling algorithm.
    We start with a given state, find all its neighbors,
    move towards the neighbor which provides the maximum (or minimum) change.
    We keep doing this until we are at a state where we do not have any
    neighbors which can improve the solution.
        Args:
            search_prob: The search state at the start.
            find_max: If True, the algorithm should find the maximum else the minimum.
            max_x, min_x, max_y, min_y: the maximum and minimum bounds of x and y.
            visualization: If True, a matplotlib graph is displayed.
            max_iter: number of times to run the iteration.
        Returns a search state having the maximum (or minimum) score.
    """
    current_state = search_prob
    scores = []  # list to store the current score at each iteration
    iterations = 0
    solution_found = False
    visited = set()
    while not solution_found and iterations < max_iter:
        visited.add(current_state)
        iterations += 1
        current_score = current_state.score()
        scores.append(current_score)
        neighbors = current_state.get_neighbors()
        max_change = -math.inf
        min_change = math.inf
        next_state = None  # to hold the next best neighbor
        for neighbor in neighbors:
            if neighbor in visited:
                continue  # do not want to visit the same state again
            if (
                neighbor.x > max_x
                or neighbor.x < min_x
                or neighbor.y > max_y
                or neighbor.y < min_y
            ):
                continue  # neighbor outside our bounds
            change = neighbor.score() - current_score
            if find_max:  # finding max
                # going to direction with greatest ascent
                if change > max_change and change > 0:
                    max_change = change
                    next_state = neighbor
            elif change < min_change and change < 0:  # finding min
                # to direction with greatest descent
                min_change = change
                next_state = neighbor
        if next_state is not None:
            # we found at least one neighbor which improved the current state
            current_state = next_state
        else:
            # since we have no neighbor that improves the solution we stop the search
            solution_found = True

    if visualization:
        from matplotlib import pyplot as plt

        plt.plot(range(iterations), scores)
        plt.xlabel("Iterations")
        plt.ylabel("Function values")
        plt.show()

    return current_state