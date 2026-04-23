def pheromone_update(
    pheromone: list[list[float]],
    cities: dict[int, list[int]],
    pheromone_evaporation: float,
    ants_route: list[list[int]],
    q: float, 
    best_path: list[int],
    best_distance: float,
) -> tuple[list[list[float]], list[int], float]:
    for a in range(len(cities)):
        for b in range(len(cities)):
            pheromone[a][b] *= pheromone_evaporation
    for ant_route in ants_route:
        total_distance = 0.0
        for i in range(len(ant_route) - 1):  
            total_distance += distance(cities[ant_route[i]], cities[ant_route[i + 1]])
        delta_pheromone = q / total_distance
        for i in range(len(ant_route) - 1): 
            pheromone[ant_route[i]][ant_route[i + 1]] += delta_pheromone
            pheromone[ant_route[i + 1]][ant_route[i]] = pheromone[ant_route[i]][
                ant_route[i + 1]
            ]

        if total_distance < best_distance:
            best_path = ant_route
            best_distance = total_distance

    return pheromone, best_path, best_distance
