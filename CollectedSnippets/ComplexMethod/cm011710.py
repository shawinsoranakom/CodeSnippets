def __init__(
        self,
        scheduler: Scheduler,
        snodes: list[BaseSchedulerNode],
        use_custom_partition_algo: bool,
        prev_node_1: BaseSchedulerNode | None = None,
        prev_node_2: BaseSchedulerNode | None = None,
        enable_autotune: bool = False,
    ) -> None:
        self.read_to_node = {}
        self.name_to_node = {}

        if prev_node_1 is None or prev_node_2 is None:
            super().__init__(scheduler, snodes)

            for node in snodes:
                for read in node.read_writes.reads:
                    self.read_to_node[read.name] = node

                for name in node.get_operation_names():
                    self.name_to_node[name] = node
        else:
            self.scheduler = scheduler
            self.snodes = snodes
            self.node = None
            self.users: list[NodeUser] = []

            self.set_read_writes(
                dependencies.ReadWrites.merge_list(
                    [prev_node_1.read_writes, prev_node_2.read_writes]
                )
            )

            self.unmet_dependencies = (
                OrderedSet(
                    dep
                    for dep in OrderedSet.union(
                        prev_node_1.unmet_dependencies, prev_node_2.unmet_dependencies
                    )
                    if dep.name not in self.get_buffer_names()
                )
                - self.read_writes.writes
            )

            self.min_order = min([prev_node_1.min_order, prev_node_2.min_order])
            self.max_order = max([prev_node_1.max_order, prev_node_2.max_order])
            self.min_input_distance = min(
                prev_node_1.min_input_distance, prev_node_2.min_input_distance
            )
            self.max_input_distance = max(
                prev_node_1.max_input_distance, prev_node_2.max_input_distance
            )

            if prev_node_1.is_foreach():
                assert isinstance(prev_node_1, ForeachKernelSchedulerNode)
                foreach_node, other_node = prev_node_1, prev_node_2
            else:
                assert isinstance(prev_node_2, ForeachKernelSchedulerNode)
                foreach_node, other_node = prev_node_2, prev_node_1

            self.ancestors = foreach_node.ancestors
            self.ancestors.update(other_node.ancestors)

            self.name_to_node = foreach_node.name_to_node
            for name in other_node.get_operation_names():
                self.name_to_node[name] = other_node

            self.outputs_by_name: dict[str, SchedulerBuffer] = {
                k: v for snode in self.snodes for k, v in snode.outputs_by_name.items()
            }

        self.use_custom_partition_algo = use_custom_partition_algo
        device = snodes[0].get_device()
        assert device
        self.group = (device, ((sympy.Expr("combo_kernel"),),))
        self.origins = OrderedSet[torch.fx.Node]()
        self.enable_autotune = enable_autotune