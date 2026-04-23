def _move_module_to_device(
    module: nn.Module,
    ignored_params: set[nn.Parameter],
    ignored_buffers: set[torch.Tensor],
    device_from_device_id: torch.device | None,
) -> None:
    """
    Move ``module`` depending on ``device_from_device_id`` and its current device.

    This includes moving ignored modules' parameters.

    - If ``device_from_device_id`` is not ``None``, then this moves
    ``module`` to the device.
    - If ``device_from_device_id`` is ``None``, then this does not move
    ``module`` but warns the user if it is on CPU.

    Precondition: ``_check_single_device_module()``.
    """
    cpu_device = torch.device("cpu")
    if device_from_device_id is not None:
        # BFS from `module` without traversing any nested FSDP instances to
        # collect the parameters/buffers that have not yet been managed
        queue: collections.deque[nn.Module] = collections.deque()
        queue.append(module)
        params: list[nn.Parameter] = []
        buffers: list[torch.Tensor] = []
        while queue:
            curr_module = queue.popleft()
            # NOTE: We include a check to only move parameters/buffers that are
            # on CPU device. If they are on a CUDA device different from the
            # one specified by `device_id`, then this does NOT move them. This
            # is so that we can raise an error in `_get_compute_device()`.
            params.extend(
                param
                for param in curr_module.parameters(recurse=False)
                if param.device == cpu_device
            )
            buffers.extend(
                buffer
                for buffer in curr_module.buffers(recurse=False)
                if buffer.device == cpu_device
            )
            for submodule in curr_module.children():
                if not isinstance(submodule, fsdp_file.FullyShardedDataParallel):
                    queue.append(submodule)
        params_to_move = [p for p in params if p not in ignored_params]
        bufs_to_move = [p for p in buffers if p not in ignored_buffers]
        _move_states_to_device(params_to_move, bufs_to_move, device_from_device_id)
        return
    param = next(_get_orig_params(module, ignored_params), None)
    if param is not None and param.device == cpu_device:
        _warn_cpu_init()