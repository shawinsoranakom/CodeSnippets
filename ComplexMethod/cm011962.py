def _extract_inputs_from_exported_gm(
    gm: GraphModule, example_inputs_: Sequence[InputType]
) -> Sequence[InputType]:
    fake_inputs = [
        node.meta.get("val") for node in gm.graph.nodes if node.op == "placeholder"
    ]

    if not config.fx_wrapper:
        # Replace non-tensor inputs with Nones
        # constant scalars embedded in the graph
        # symbolic scalars (symint) are not supported in non-fx_wrapper mode
        fake_inputs = [
            inp if isinstance(inp, torch.Tensor) else None for inp in fake_inputs
        ]

    if any(v is not None for v in fake_inputs):
        # Validate devices before switching to fake tensors.
        for idx, fi, i in zip(count(), fake_inputs, example_inputs_):
            if fi is not None and isinstance(fi, torch.Tensor):
                assert isinstance(i, torch.Tensor)
                if fi.device != i.device:
                    raise ValueError(
                        f"Device mismatch between fake input and example input at position #{idx}: "
                        f"{fi.device} vs {i.device}. If the model was exported via torch.export(), "
                        "make sure torch.export() and torch.aot_compile() run on the same device."
                    )
        return fake_inputs

    return example_inputs_