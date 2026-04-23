def _detect_fake_mode_from_gm(
    gm: torch.fx.GraphModule,
) -> torch._subclasses.fake_tensor.FakeTensorMode | None:
    """
    For a given graph module, we look at the "val" of placeholder nodes to find the fake inputs.
    Additionally, if gm doesn't have placeholders, we further look at the "example_value" or "val" of other nodes.
    If no fake mode is found, we return None for fake_mode.
    """

    fake_inps: list[torch.Tensor] = []
    fake_vals: list[torch.Tensor] = []
    for node in gm.graph.nodes:
        if node.op == "placeholder" and "val" in node.meta:
            fake_val = node.meta["val"]
            if fake_val is not None and isinstance(fake_val, torch.Tensor):
                fake_inps.append(fake_val)
        elif len(fake_inps) == 0 and (
            "example_value" in node.meta or "val" in node.meta
        ):
            fake_val = None
            if "example_value" in node.meta:
                fake_val = node.meta["example_value"]
            elif "val" in node.meta:
                fake_val = node.meta["val"]
            if fake_val is not None and isinstance(fake_val, torch.Tensor):
                fake_vals.append(fake_val)

    return detect_fake_mode(fake_inps + fake_vals)