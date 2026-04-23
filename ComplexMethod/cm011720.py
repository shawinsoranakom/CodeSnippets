def merge_loops(self) -> None:
        if not config.loop_ordering_after_fusion:
            return

        for node in self.nodes:
            # Even for CPU, if we are using the halide backend, we still need
            # the merge loops steps below
            if not isinstance(node, (SchedulerNode, FusedSchedulerNode)) or (
                not node.is_gpu() and config.cpu_backend != "halide"
            ):
                continue
            for snode in node.get_nodes():
                # merge loops for the scheduler node
                if not isinstance(snode, SchedulerNode) or snode.is_template():
                    continue

                snode.merge_loops()