def get_distance(highway_now: list, car_index: int) -> int:
 

    distance = 0
    cells = highway_now[car_index + 1 :]
    for cell in range(len(cells)): 
        if cells[cell] != -1: 
            return distance
        distance += 1

  return distance + get_distance(highway_now, -1)
