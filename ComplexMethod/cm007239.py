def get_vertex_neighbors(self, vertex: Vertex) -> dict[Vertex, int]:
        """Returns a dictionary mapping each direct neighbor of a vertex to the count of connecting edges.

        A neighbor is any vertex directly connected to the input vertex, either as a source or target.
        The count reflects the number of edges between the input vertex and each neighbor.
        """
        neighbors: dict[Vertex, int] = {}
        for edge in self.edges:
            if edge.source_id == vertex.id:
                neighbor = self.get_vertex(edge.target_id)
                if neighbor is None:
                    continue
                if neighbor not in neighbors:
                    neighbors[neighbor] = 0
                neighbors[neighbor] += 1
            elif edge.target_id == vertex.id:
                neighbor = self.get_vertex(edge.source_id)
                if neighbor is None:
                    continue
                if neighbor not in neighbors:
                    neighbors[neighbor] = 0
                neighbors[neighbor] += 1
        return neighbors