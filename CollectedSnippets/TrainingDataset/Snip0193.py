def simulate(
    highway: list, number_of_update: int, probability: float, max_speed: int
) -> list:

    number_of_cells = len(highway[0])

    for i in range(number_of_update):
        next_speeds_calculated = update(highway[i], probability, max_speed)
        real_next_speeds = [-1] * number_of_cells

        for car_index in range(number_of_cells):
            speed = next_speeds_calculated[car_index]
            if speed != -1:
                index = (car_index + speed) % number_of_cells
                real_next_speeds[index] = speed
        highway.append(real_next_speeds)

    return highway
