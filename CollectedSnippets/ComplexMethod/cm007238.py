def get_all_successors(self, vertex: Vertex, *, recursive=True, flat=True, visited=None):
        """Returns all successors of a given vertex, optionally recursively and as a flat or nested list.

        Args:
            vertex: The vertex whose successors are to be retrieved.
            recursive: If True, retrieves successors recursively; otherwise, only immediate successors.
            flat: If True, returns a flat list of successors; if False, returns a nested list structure.
            visited: Internal set used to track visited vertices and prevent cycles.

        Returns:
            A list of successor vertices, either flat or nested depending on the `flat` parameter.
        """
        if visited is None:
            visited = set()

        # Prevent revisiting vertices to avoid infinite loops in cyclic graphs
        if vertex in visited:
            return []

        visited.add(vertex)

        successors = vertex.successors
        if not successors:
            return []

        successors_result = []

        for successor in successors:
            if recursive:
                next_successors = self.get_all_successors(successor, recursive=recursive, flat=flat, visited=visited)
                if flat:
                    successors_result.extend(next_successors)
                else:
                    successors_result.append(next_successors)
            if flat:
                successors_result.append(successor)
            else:
                successors_result.append([successor])

        if not flat and successors_result:
            return [successors, *successors_result]

        return successors_result