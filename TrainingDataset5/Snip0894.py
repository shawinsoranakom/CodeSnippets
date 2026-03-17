def dfs_recursive(self, start_vertex: int, visited: list) -> None:
    visited[start_vertex] = True

    print(start_vertex, end="")
    for i in self.vertex:
        if not visited[i]:
            print(" ", end="")
            self.dfs_recursive(i, visited)
