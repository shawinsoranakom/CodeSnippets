def add_edge(
        self, source_vertex: T, destination_vertex: T
    ) -> GraphAdjacencyList[T]:
        """
        Connects vertices together. Creates and Edge from source vertex to destination
        vertex.
        Vertices will be created if not found in graph
        """

        if not self.directed:  # For undirected graphs
            # if both source vertex and destination vertex are both present in the
            # adjacency list, add destination vertex to source vertex list of adjacent
            # vertices and add source vertex to destination vertex list of adjacent
            # vertices.
            if source_vertex in self.adj_list and destination_vertex in self.adj_list:
                self.adj_list[source_vertex].append(destination_vertex)
                self.adj_list[destination_vertex].append(source_vertex)
            # if only source vertex is present in adjacency list, add destination vertex
            # to source vertex list of adjacent vertices, then create a new vertex with
            # destination vertex as key and assign a list containing the source vertex
            # as it's first adjacent vertex.
            elif source_vertex in self.adj_list:
                self.adj_list[source_vertex].append(destination_vertex)
                self.adj_list[destination_vertex] = [source_vertex]
            # if only destination vertex is present in adjacency list, add source vertex
            # to destination vertex list of adjacent vertices, then create a new vertex
            # with source vertex as key and assign a list containing the source vertex
            # as it's first adjacent vertex.
            elif destination_vertex in self.adj_list:
                self.adj_list[destination_vertex].append(source_vertex)
                self.adj_list[source_vertex] = [destination_vertex]
            # if both source vertex and destination vertex are not present in adjacency
            # list, create a new vertex with source vertex as key and assign a list
            # containing the destination vertex as it's first adjacent vertex also
            # create a new vertex with destination vertex as key and assign a list
            # containing the source vertex as it's first adjacent vertex.
            else:
                self.adj_list[source_vertex] = [destination_vertex]
                self.adj_list[destination_vertex] = [source_vertex]
        # For directed graphs
        # if both source vertex and destination vertex are present in adjacency
        # list, add destination vertex to source vertex list of adjacent vertices.
        elif source_vertex in self.adj_list and destination_vertex in self.adj_list:
            self.adj_list[source_vertex].append(destination_vertex)
        # if only source vertex is present in adjacency list, add destination
        # vertex to source vertex list of adjacent vertices and create a new vertex
        # with destination vertex as key, which has no adjacent vertex
        elif source_vertex in self.adj_list:
            self.adj_list[source_vertex].append(destination_vertex)
            self.adj_list[destination_vertex] = []
        # if only destination vertex is present in adjacency list, create a new
        # vertex with source vertex as key and assign a list containing destination
        # vertex as first adjacent vertex
        elif destination_vertex in self.adj_list:
            self.adj_list[source_vertex] = [destination_vertex]
        # if both source vertex and destination vertex are not present in adjacency
        # list, create a new vertex with source vertex as key and a list containing
        # destination vertex as it's first adjacent vertex. Then create a new vertex
        # with destination vertex as key, which has no adjacent vertex
        else:
            self.adj_list[source_vertex] = [destination_vertex]
            self.adj_list[destination_vertex] = []

        return self