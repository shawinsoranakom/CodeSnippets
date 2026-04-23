def fix_iota_device(match: Match, length, start, step, dtype, device, requires_grad):
    """
    Eager supports:

        aten.index(cuda_tensor, torch.arange(..., device="cpu"))

    But this results in an implicit host-device-copy and breaks cudagraphs.
    Rewrite the arange to use CUDA.
    """
    (node,) = match.nodes
    user_devices = OrderedSet[torch.device]()
    for user in node.users:
        if (
            user.op == "call_function"
            and user.target in (aten.index.Tensor, aten.index_put.default)
            and hasattr(user.meta.get("val"), "device")
        ):
            user_devices.add(user.meta["val"].device)  # type: ignore[union-attr]
        else:
            return  # bail out

    if len(user_devices) == 1 and "val" in node.meta:
        (user_device,) = user_devices
        if device.type != user_device.type:
            repl = match.graph.call_function(
                torch.ops.prims.iota.default,
                (length,),
                {
                    "start": start,
                    "step": step,
                    "dtype": dtype,
                    "device": user_device,
                    "requires_grad": requires_grad,
                },
            )
            repl.meta.update(node.meta)
            repl.meta["val"] = repl.meta["val"].to(user_device)
            node.replace_all_uses_with(repl)
            match.erase_nodes()