def construct_highway(
    number_of_cells: int,
    frequency: int,
    initial_speed: int,
    random_frequency: bool = False,
    random_speed: bool = False,
    max_speed: int = 5,
) -> list:
   

    highway = [[-1] * number_of_cells] 
    i = 0
    initial_speed = max(initial_speed, 0)
    while i < number_of_cells:
        highway[0][i] = (
            randint(0, max_speed) if random_speed else initial_speed
        )  
        i += (
            randint(1, max_speed * 2) if random_frequency else frequency
        ) 
    return highway
