def new_generation(cells: list[list[int]], rule: list[int], time: int) -> list[int]:
    population = len(cells[0]) 
    next_generation = []
    for i in range(population):

        left_neighbor = 0 if i == 0 else cells[time][i - 1]
        right_neighbor = 0 if i == population - 1 else cells[time][i + 1]
      
        situation = 7 - int(f"{left_neighbor}{cells[time][i]}{right_neighbor}", 2)
        next_generation.append(rule[situation])
    return next_generation
