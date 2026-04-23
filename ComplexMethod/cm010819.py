def _get_partition_fn(
    fw_hop_node: torch.fx.Node, aot_config: AOTConfig
) -> tuple[bool, Callable[..., tuple[torch.fx.GraphModule, torch.fx.GraphModule]]]:
    """
    Return either the default `partition_fn` in aot_config or a HOP specific partition
    function.

    If a HOP specific partition function is returned, used_hop_custom_partition is True.

    See Note [InvokeSubgraphHOP Partitioner]
    """
    used_hop_custom_partition = False
    if aot_config.partition_fn is None:
        raise AssertionError("aot_config.partition_fn must not be None")
    partition_fn: Callable[..., tuple[torch.fx.GraphModule, torch.fx.GraphModule]] = (
        aot_config.partition_fn
    )
    if (
        fw_hop_node.target == torch._higher_order_ops.invoke_subgraph
        and "custom" in fw_hop_node.meta
        and "nested_region_config" in fw_hop_node.meta["custom"]
    ):
        hop_partition_fn = fw_hop_node.meta["custom"][
            "nested_region_config"
        ].partitioner
        if hop_partition_fn is None:
            # inherit the parent paritioner
            return used_hop_custom_partition, partition_fn

        if callable(hop_partition_fn):
            partition_fn = hop_partition_fn  # pyrefly: ignore [bad-assignment]
            used_hop_custom_partition = True
        else:
            if not isinstance(hop_partition_fn, str):
                raise AssertionError(
                    f"expected hop_partition_fn to be str, got {type(hop_partition_fn)}"
                )
            match hop_partition_fn:
                case "default_partition":
                    partition_fn = torch._functorch.partitioners.default_partition
                case "min_cut_rematerialization_partition":
                    partition_fn = torch._functorch.partitioners.min_cut_rematerialization_partition
                case _:
                    raise ValueError(
                        f"Unknown HOP partitioner config: {hop_partition_fn}"
                    )
    return used_hop_custom_partition, partition_fn