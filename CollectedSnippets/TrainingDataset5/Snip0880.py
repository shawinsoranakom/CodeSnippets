def bfs(self, start_vertex: int) -> set[int]:
    visited = set()
 
    queue: Queue = Queue()
 
    visited.add(start_vertex)
    queue.put(start_vertex)

    while not queue.empty():
        vertex = queue.get()
 
        for adjacent_vertex in self.vertices[vertex]:
            if adjacent_vertex not in visited:
                queue.put(adjacent_vertex)
                visited.add(adjacent_vertex)
    return visited
