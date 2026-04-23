def simulated_annealing(
    search_prob,
    find_max: bool = True,
    max_x: float = math.inf,
    min_x: float = -math.inf,
    max_y: float = math.inf,
    min_y: float = -math.inf,
    visualization: bool = False,
    start_temperate: float = 100,
    rate_of_decrease: float = 0.01,
    threshold_temp: float = 1,
) -> Any:
    """
    Implementation of the simulated annealing algorithm. We start with a given state,
    find all its neighbors. Pick a random neighbor, if that neighbor improves the
    solution, we move in that direction, if that neighbor does not improve the solution,
    we generate a random real number between 0 and 1, if the number is within a certain
    range (calculated using temperature) we move in that direction, else we pick
    another neighbor randomly and repeat the process.

    Args:
        search_prob: The search state at the start.
        find_max: If True, the algorithm should find the minimum else the minimum.
        max_x, min_x, max_y, min_y: the maximum and minimum bounds of x and y.
        visualization: If True, a matplotlib graph is displayed.
        start_temperate: the initial temperate of the system when the program starts.
        rate_of_decrease: the rate at which the temperate decreases in each iteration.
        threshold_temp: the threshold temperature below which we end the search
    Returns a search state having the maximum (or minimum) score.
    """
    search_end = False
    current_state = search_prob
    current_temp = start_temperate
    scores = []
    iterations = 0
    best_state = None

    while not search_end:
        current_score = current_state.score()
        if best_state is None or current_score > best_state.score():
            best_state = current_state
        scores.append(current_score)
        iterations += 1
        next_state = None
        neighbors = current_state.get_neighbors()
        while (
            next_state is None and neighbors
        ):  # till we do not find a neighbor that we can move to
            index = random.randint(0, len(neighbors) - 1)  # picking a random neighbor
            picked_neighbor = neighbors.pop(index)
            change = picked_neighbor.score() - current_score

            if (
                picked_neighbor.x > max_x
                or picked_neighbor.x < min_x
                or picked_neighbor.y > max_y
                or picked_neighbor.y < min_y
            ):
                continue  # neighbor outside our bounds

            if not find_max:
                change = change * -1  # in case we are finding minimum
            if change > 0:  # improves the solution
                next_state = picked_neighbor
            else:
                probability = (math.e) ** (
                    change / current_temp
                )  # probability generation function
                if random.random() < probability:  # random number within probability
                    next_state = picked_neighbor
        current_temp = current_temp - (current_temp * rate_of_decrease)

        if current_temp < threshold_temp or next_state is None:
            # temperature below threshold, or could not find a suitable neighbor
            search_end = True
        else:
            current_state = next_state

    if visualization:
        from matplotlib import pyplot as plt

        plt.plot(range(iterations), scores)
        plt.xlabel("Iterations")
        plt.ylabel("Function values")
        plt.show()
    return best_state