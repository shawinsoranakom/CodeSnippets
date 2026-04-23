def _manual_reorder_graph(self) -> None:
        """
        Reorder nodes in the FX graph to enforce manual overlap dependencies.

        forward graph (all-gathers only):
            modules are processed in order: module 0, 1, 2, ...

            before reordering:
            ag_start_0 -> ag_wait_0 -> compute_0 -> ag_start_1 -> ag_wait_1 -> compute_1 -> ...

            Reordering prefetches module i+1's parameters while computing module i
            It adds dependencies: ag_wait_i should depend on ag_start_(i+1)
            This enforces ag_start_(i+1) to happen before ag_wait_i so it overlaps with module i's compute

            after reordering:
            ag_start_0 -> ag_start_1 -> ag_wait_0 -> compute_0 -> ag_wait_1 -> compute_1 -> ...

        backward graph (all-gathers and reduce-scatters):
            modules are processed in reverse order: module N, N-1, N-2, ...

            before reordering:
            ag_start_N -> ag_wait_N -> compute_N -> rs_start_N -> rs_wait_N -> ...

            For all-gathers, prefetch module i-1's parameters while computing module i
            Adds dependencies: ag_wait_i should depend on ag_start_(i-1)
            So ag_start_(i-1) overlaps with module i's compute

            For reduce-scatters, defer rs_wait_i to happen after rs_start_(i-1)
            Adds dependencies: rs_wait_i should depend on rs_start_(i-1)
            So rs_start_i overlaps with module i-1's compute

        """
        delayed_rs_wait_nodes: list[fx.Node] = []
        current_rs_start_nodes: list[fx.Node] = []
        overlap_deps: dict[fx.Node, OrderedSet[fx.Node]] = defaultdict(OrderedSet)

        # Re-initialize after graph modification in _manual_bucket_collectives
        self.node_idx = {n: i for i, n in enumerate(self.nodes)}
        self.on_path_ready = []
        self.scheduled = OrderedSet()
        for node in self.nodes:
            if self.in_degree[node] == 0:
                self._add_to_ready_queue(node)

        # schedule reduce scatter normally in self._schedule
        while self.on_path_ready:
            _, node = heapq.heappop(self.on_path_ready)
            node_type = self.bucketer.bucketed_node_types.get(node, "")

            if node in self.scheduled:
                continue

            if node_type == "bucketed_reduce_scatter":
                # Collect reduce scatter start nodes (pre_bucket_rs and rs)
                current_rs_start_nodes.append(node)

            elif node_type == "bucketed_reduce_scatter_wait":
                # When we see a wait node from a new RS, flush delayed waits
                # with dependencies on previously collected RS start nodes
                if current_rs_start_nodes:
                    for delayed in delayed_rs_wait_nodes:
                        for rs_start in current_rs_start_nodes:
                            overlap_deps[delayed].add(rs_start)
                    delayed_rs_wait_nodes.clear()
                    current_rs_start_nodes.clear()
                delayed_rs_wait_nodes.append(node)

            self._schedule(node)

        self.scheduled = OrderedSet(reversed(list(self.scheduled)))
        picked_ag: list[fx.Node] = []
        last_compute: fx.Node | None = None

        for node in self.scheduled:
            node_type = self.bucketer.bucketed_node_types.get(node, "")
            if node_type == "bucketed_all_gather":
                picked_ag.append(node)
                continue

            if node_type == "bucketed_all_gather_wait":
                # Connect corresponding all_gather_wait -> all_gather edges
                if picked_ag:
                    for ag in picked_ag:
                        overlap_deps[self.bucketer.node_to_wait_map[node]].add(ag)
                picked_ag.clear()
            if is_compute_node(node):
                last_compute = node

        if last_compute is not None and not bool(
            OrderedSet(picked_ag) & OrderedSet(self.node_ancestors[last_compute])
        ):
            for ag in picked_ag:
                overlap_deps[last_compute].add(ag)

        _stable_topological_sort(self.graph, overlap_deps)
        self.graph.lint()

        if self.insert_overlap_deps:
            from torch._inductor.fx_passes.control_dependencies import (
                preserve_node_ordering,
            )

            preserve_node_ordering(self.graph, overlap_deps)