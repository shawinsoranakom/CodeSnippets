def get_shortest_path(self, start_vertex: int, finish_vertex: int) -> int | None:
    queue = deque([start_vertex])
    distances: list[int | None] = [None] * self.size
    distances[start_vertex] = 0

    while queue:
        current_vertex = queue.popleft()
        current_distance = distances[current_vertex]
        if current_distance is None:
            continue

        for edge in self[current_vertex]:
            new_distance = current_distance + edge.weight
            dest_vertex_distance = distances[edge.destination_vertex]
            if (
                isinstance(dest_vertex_distance, int)
                and new_distance >= dest_vertex_distance
            ):
                continue
            distances[edge.destination_vertex] = new_distance
            if edge.weight == 0:
                queue.appendleft(edge.destination_vertex)
            else:
                queue.append(edge.destination_vertex)

    if distances[finish_vertex] is None:
        raise ValueError("No path from start_vertex to finish_vertex.")

    return distances[finish_vertex]
