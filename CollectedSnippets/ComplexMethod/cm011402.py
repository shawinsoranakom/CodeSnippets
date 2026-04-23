def _prep_arguments(
    op_call_repr: str,
    args: tuple[object, ...],
    kwargs: dict[str, object] | None,
) -> tuple[
    torch.Tensor,
    torch.Size,
    "torch.distributed.device_mesh.DeviceMesh",
    tuple[Placement, ...],
    int | None,
    bool,
]:
    """
    Prepare arguments for nonlinear reduction ops.

    Returns:
        local_tensor: The local tensor to operate on
        global_shape: The global shape of the DTensor
        device_mesh: The device mesh
        placements: The placements tuple
        dim: The reduction dimension (can be None)
        keepdim: Whether to keep the reduced dimension
    """
    input_dtensor = cast(dtensor.DTensor, args[0])
    dim: int | None = None
    keepdim: bool = False

    if not isinstance(input_dtensor, dtensor.DTensor):
        raise NotImplementedError
    if len(args) > 1:
        dim = cast(int, args[1])
    if len(args) > 2:
        keepdim = cast(bool, args[2])
    if kwargs:
        if "dim" in kwargs:
            dim = cast(int, kwargs["dim"])
        if "keepdim" in kwargs:
            keepdim = cast(bool, kwargs["keepdim"])
    device_mesh = input_dtensor.device_mesh
    placements = input_dtensor.placements

    # check for partial placements and handle it as a replicate.
    if any(isinstance(p, Partial) for p in placements):
        target_placements = [
            Replicate() if isinstance(p, Partial) else p for p in placements
        ]
        input_dtensor = input_dtensor.redistribute(
            device_mesh=device_mesh, placements=target_placements
        )
        placements = input_dtensor.placements
    local_tensor = input_dtensor.to_local()
    global_shape = input_dtensor.shape

    return local_tensor, global_shape, device_mesh, placements, dim, keepdim