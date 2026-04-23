def max_flow(self, source, sink):
        flow, self.q[0] = 0, source
        for l in range(31):  # l = 30 maybe faster for random data  # noqa: E741
            while True:
                self.lvl, self.ptr = [0] * len(self.q), [0] * len(self.q)
                qi, qe, self.lvl[source] = 0, 1, 1
                while qi < qe and not self.lvl[sink]:
                    v = self.q[qi]
                    qi += 1
                    for e in self.adj[v]:
                        if not self.lvl[e[0]] and (e[2] - e[3]) >> (30 - l):
                            self.q[qe] = e[0]
                            qe += 1
                            self.lvl[e[0]] = self.lvl[v] + 1

                p = self.depth_first_search(source, sink, INF)
                while p:
                    flow += p
                    p = self.depth_first_search(source, sink, INF)

                if not self.lvl[sink]:
                    break

        return flow