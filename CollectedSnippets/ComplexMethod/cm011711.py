def combinable_nodes(
        cls, nodes: list[BaseSchedulerNode]
    ) -> list[BaseSchedulerNode]:
        extern = [x for x in nodes if isinstance(x, ExternKernelSchedulerNode)]
        if extern:
            log.debug(
                "ComboKernels: %d external nodes are filtered %s",
                len(extern),
                [node.node.get_origins() for node in extern if node.node is not None],
            )
        grouped = [x for x in nodes if isinstance(x, GroupedSchedulerNode)]
        if grouped:
            log.debug(
                "ComboKernels: %d grouped nodes are filtered",
                len(grouped),
            )
        mix_order = [x for x in nodes if isinstance(x, FusedMixOrderReductions)]
        if mix_order:
            log.debug(
                "ComboKernels: %d FusedMixOrderReductions nodes are filtered",
                len(mix_order),
            )

        filtered_nodes = [
            x
            for x in nodes
            if not isinstance(
                x,
                (
                    NopKernelSchedulerNode,
                    ExternKernelSchedulerNode,
                    GroupedSchedulerNode,
                    FusedMixOrderReductions,
                ),
            )
        ]
        foreach_nodes = [
            x for x in filtered_nodes if isinstance(x, ForeachKernelSchedulerNode)
        ]
        if foreach_nodes:
            log.debug("ComboKernels: %d foreach nodes are filtered", len(foreach_nodes))
        filtered_nodes = [
            x for x in filtered_nodes if not isinstance(x, ForeachKernelSchedulerNode)
        ]
        template_nodes = [x for x in filtered_nodes if x.is_template()]
        if template_nodes:
            log.debug(
                "ComboKernels: %d template nodes are filtered: %s",
                len(template_nodes),
                template_nodes,
            )
        filtered_nodes = [x for x in filtered_nodes if x not in template_nodes]

        # Filter out reduction nodes if combo_kernels_pointwise_only is enabled
        if config.combo_kernels_pointwise_only:
            reduction_nodes = [x for x in filtered_nodes if x.is_reduction()]
            if reduction_nodes:
                log.debug(
                    "ComboKernels: %d reduction nodes are filtered (pointwise_only mode)",
                    len(reduction_nodes),
                )
            filtered_nodes = [x for x in filtered_nodes if not x.is_reduction()]

        return filtered_nodes