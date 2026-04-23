def scoop_regions(gm: torch.fx.GraphModule) -> torch.fx.GraphModule:
        from torch.fx.passes.infra.partitioner import CapabilityBasedPartitioner
        from torch.fx.passes.operator_support import create_op_support
        from torch.fx.passes.utils.fuser_utils import fuse_by_partitions

        # Group tagged nodes by region ID.  The region ID comes from the
        # optional "inductor_region" key inside the compile_with_inductor
        # annotation. When absent, all tagged nodes share a single default region
        _DEFAULT_REGION = object()
        regions: dict[object, set[torch.fx.Node]] = {}
        for node in gm.graph.nodes:
            if _needs_inductor_compile(node):
                compile_value = node.meta["custom"]["compile_with_inductor"]
                if (
                    isinstance(compile_value, dict)
                    and "inductor_region" in compile_value
                ):
                    rid = compile_value["inductor_region"]
                else:
                    rid = _DEFAULT_REGION
                regions.setdefault(rid, set()).add(node)

        if not regions:
            logger.info("No inductor marked nodes found")
            return gm

        # Run CapabilityBasedPartitioner per region to get cycle-safe partitions
        # without merging across region boundaries.
        def _is_in_region(
            region_nodes: set[torch.fx.Node],
        ) -> Callable[[Mapping[str, torch.nn.Module], torch.fx.Node], bool]:
            def is_node_supported(
                _submodules: Mapping[str, torch.nn.Module], node: torch.fx.Node
            ) -> bool:
                return node in region_nodes

            return is_node_supported

        all_partitions: list[dict[torch.fx.Node, int | None]] = []
        for region_nodes in regions.values():
            support = create_op_support(_is_in_region(region_nodes))
            partitioner = CapabilityBasedPartitioner(
                gm, support, allows_single_node_partition=True
            )
            for partition in partitioner.propose_partitions():
                all_partitions.append(partition.nodes)

        return fuse_by_partitions(
            gm,
            all_partitions,
            prefix="__marked_inductor_submod",
            always_return_tuple=True,
        )