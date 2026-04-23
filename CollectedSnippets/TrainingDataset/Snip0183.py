def new_generation(cells: list[list[int]]) -> list[list[int]]:
   
    next_generation = []
    for i in range(len(cells)):
        next_generation_row = []
        for j in range(len(cells[i])):
          
            neighbour_count = 0
            if i > 0 and j > 0:
                neighbour_count += cells[i - 1][j - 1]
            if i > 0:
                neighbour_count += cells[i - 1][j]
            if i > 0 and j < len(cells[i]) - 1:
                neighbour_count += cells[i - 1][j + 1]
            if j > 0:
                neighbour_count += cells[i][j - 1]
            if j < len(cells[i]) - 1:
                neighbour_count += cells[i][j + 1]
            if i < len(cells) - 1 and j > 0:
                neighbour_count += cells[i + 1][j - 1]
            if i < len(cells) - 1:
                neighbour_count += cells[i + 1][j]
            if i < len(cells) - 1 and j < len(cells[i]) - 1:
                neighbour_count += cells[i + 1][j + 1]

            alive = cells[i][j] == 1
            if (alive and 2 <= neighbour_count <= 3) or (
                not alive and neighbour_count == 3
            ):
                next_generation_row.append(1)
            else:
                next_generation_row.append(0)

        next_generation.append(next_generation_row)
    return next_generation
