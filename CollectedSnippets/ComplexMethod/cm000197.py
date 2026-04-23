def get_shortest_path(self, start_vertex: int, finish_vertex: int) -> int | None:
        """
        Return the shortest distance from start_vertex to finish_vertex in 0-1-graph.
              1                  1         1
         0--------->3        6--------7>------->8
         |          ^        ^        ^         |1
         |          |        |        |0        v
        0|          |0      1|        9-------->10
         |          |        |        ^    1
         v          |        |        |0
         1--------->2<-------4------->5
              0         1        1
        >>> g = AdjacencyList(11)
        >>> g.add_edge(0, 1, 0)
        >>> g.add_edge(0, 3, 1)
        >>> g.add_edge(1, 2, 0)
        >>> g.add_edge(2, 3, 0)
        >>> g.add_edge(4, 2, 1)
        >>> g.add_edge(4, 5, 1)
        >>> g.add_edge(4, 6, 1)
        >>> g.add_edge(5, 9, 0)
        >>> g.add_edge(6, 7, 1)
        >>> g.add_edge(7, 8, 1)
        >>> g.add_edge(8, 10, 1)
        >>> g.add_edge(9, 7, 0)
        >>> g.add_edge(9, 10, 1)
        >>> g.add_edge(1, 2, 2)
        Traceback (most recent call last):
            ...
        ValueError: Edge weight must be either 0 or 1.
        >>> g.get_shortest_path(0, 3)
        0
        >>> g.get_shortest_path(0, 4)
        Traceback (most recent call last):
            ...
        ValueError: No path from start_vertex to finish_vertex.
        >>> g.get_shortest_path(4, 10)
        2
        >>> g.get_shortest_path(4, 8)
        2
        >>> g.get_shortest_path(0, 1)
        0
        >>> g.get_shortest_path(1, 0)
        Traceback (most recent call last):
            ...
        ValueError: No path from start_vertex to finish_vertex.
        """
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