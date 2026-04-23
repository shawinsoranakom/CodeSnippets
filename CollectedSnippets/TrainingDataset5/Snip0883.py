def breath_first_search(self) -> None:
    visited = {self.source_vertex}
    self.parent[self.source_vertex] = None
    queue = [self.source_vertex] 
    while queue:
        vertex = queue.pop(0)
        for adjacent_vertex in self.graph[vertex]:
            if adjacent_vertex not in visited:
                visited.add(adjacent_vertex)
                self.parent[adjacent_vertex] = vertex
                queue.append(adjacent_vertex)
