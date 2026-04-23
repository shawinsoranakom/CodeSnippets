def _normalize_graph(self, sources, sinks):
        if sources is int:
            sources = [sources]
        if sinks is int:
            sinks = [sinks]

        if len(sources) == 0 or len(sinks) == 0:
            return

        self.source_index = sources[0]
        self.sink_index = sinks[0]

        # make fake vertex if there are more
        # than one source or sink
        if len(sources) > 1 or len(sinks) > 1:
            max_input_flow = 0
            for i in sources:
                max_input_flow += sum(self.graph[i])

            size = len(self.graph) + 1
            for room in self.graph:
                room.insert(0, 0)
            self.graph.insert(0, [0] * size)
            for i in sources:
                self.graph[0][i + 1] = max_input_flow
            self.source_index = 0

            size = len(self.graph) + 1
            for room in self.graph:
                room.append(0)
            self.graph.append([0] * size)
            for i in sinks:
                self.graph[i + 1][size - 1] = max_input_flow
            self.sink_index = size - 1