def dijkstra(self, src):
    self.par = [-1] * self.num_nodes
    self.dist[src] = 0
    q = PriorityQueue()
    q.insert((0, src))  
    for u in self.adjList:
        if u != src:
            self.dist[u] = sys.maxsize  
            self.par[u] = -1

    while not q.is_empty():
        u = q.extract_min() 
        for v, w in self.adjList[u]:
            new_dist = self.dist[u] + w
            if self.dist[v] > new_dist:
                if self.dist[v] == sys.maxsize:
                    q.insert((new_dist, v))
                else:
                    q.decrease_key((self.dist[v], v), new_dist)
                self.dist[v] = new_dist
                self.par[v] = u

    self.show_distances(src)
