def boruvka_mst(graph):
        """
        Implementation of Boruvka's algorithm
        >>> g = Graph()
        >>> g = Graph.build([0, 1, 2, 3], [[0, 1, 1], [0, 2, 1],[2, 3, 1]])
        >>> g.distinct_weight()
        >>> bg = Graph.boruvka_mst(g)
        >>> print(bg)
        1 -> 0 == 1
        2 -> 0 == 2
        0 -> 1 == 1
        0 -> 2 == 2
        3 -> 2 == 3
        2 -> 3 == 3
        """
        num_components = graph.num_vertices

        union_find = Graph.UnionFind()
        mst_edges = []
        while num_components > 1:
            cheap_edge = {}
            for vertex in graph.get_vertices():
                cheap_edge[vertex] = -1

            edges = graph.get_edges()
            for edge in edges:
                head, tail, weight = edge
                edges.remove((tail, head, weight))
            for edge in edges:
                head, tail, weight = edge
                set1 = union_find.find(head)
                set2 = union_find.find(tail)
                if set1 != set2:
                    if cheap_edge[set1] == -1 or cheap_edge[set1][2] > weight:
                        cheap_edge[set1] = [head, tail, weight]

                    if cheap_edge[set2] == -1 or cheap_edge[set2][2] > weight:
                        cheap_edge[set2] = [head, tail, weight]
            for head_tail_weight in cheap_edge.values():
                if head_tail_weight != -1:
                    head, tail, weight = head_tail_weight
                    if union_find.find(head) != union_find.find(tail):
                        union_find.union(head, tail)
                        mst_edges.append(head_tail_weight)
                        num_components = num_components - 1
        mst = Graph.build(edges=mst_edges)
        return mst