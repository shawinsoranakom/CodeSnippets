def get_inputs_devices(
    inputs: collections.abc.Sequence[object],
    model: torch.fx.GraphModule,
) -> list[torch.device | None]:
    all_inputs = pytree.tree_flatten(inputs)[0] + [
        node.meta["val"] for node in list(model.graph.nodes) if "val" in node.meta
    ]
    devices: list[torch.device | None] = list(
        OrderedSet([i.device for i in all_inputs if hasattr(i, "device")])
    )
    return [
        i for i in devices if (isinstance(i, torch.device) and i.type != "meta")
    ] + [None]