def _apply_deps_and_effect_tokens(self) -> None:
        """Apply topological sort and effect tokens to preserve overlap."""
        from torch._dynamo.graph_deduplication import _stable_topological_sort

        # Clean up any remaining erased node references and cycles
        self.aug_graph.remove_erased_extra_deps()
        autofix = torch._inductor.config.aten_distributed_optimizations.overlap_scheduling_autofix_cycles
        self.aug_graph.check_and_maybe_autofix_cyclic_extra_deps(autofix=autofix)
        additional_deps = self.aug_graph.get_all_extra_deps()

        for n, deps in additional_deps.items():
            torch._check(
                not n._erased, lambda: f"Erased node deps not transferred: {n}"
            )
            for d in deps:
                torch._check(
                    not d._erased, lambda: f"Erased node deps not transferred: {d}"
                )

        _stable_topological_sort(self.graph, additional_deps)

        if self.insert_overlap_deps:
            # Filter out collective-to-collective deps (handled by NCCL stream ordering)
            filtered_deps: dict[fx.Node, OrderedSet[fx.Node]] = {}
            for node, deps in additional_deps.items():
                filtered_node_deps: OrderedSet[fx.Node] = OrderedSet()
                for dep in deps:
                    if not (is_collective_or_wait(node) and is_collective_or_wait(dep)):
                        filtered_node_deps.add(dep)
                if filtered_node_deps:
                    filtered_deps[node] = filtered_node_deps

            if filtered_deps:
                from torch._inductor.fx_passes.control_dependencies import (
                    preserve_node_ordering,
                )

                preserve_node_ordering(self.graph, filtered_deps)