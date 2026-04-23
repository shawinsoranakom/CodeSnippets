def update(highway_now: list, probability: float, max_speed: int) -> list:
   

    number_of_cells = len(highway_now)
    next_highway = [-1] * number_of_cells

    for car_index in range(number_of_cells):
        if highway_now[car_index] != -1:
            next_highway[car_index] = min(highway_now[car_index] + 1, max_speed)
            dn = get_distance(highway_now, car_index) - 1
            next_highway[car_index] = min(next_highway[car_index], dn)
            if random() < probability:
                next_highway[car_index] = max(next_highway[car_index] - 1, 0)
    return next_highway
