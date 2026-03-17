def print_distance(distance: list[float], src):
    print(f"Vertex\tShortest Distance from vertex {src}")
    for i, d in enumerate(distance):
        print(f"{i}\t\t{d}")
