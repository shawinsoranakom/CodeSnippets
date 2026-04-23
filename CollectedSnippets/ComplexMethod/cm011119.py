def _sync_module_params_and_buffers(
    module: nn.Module,
    params: list[nn.Parameter],
    process_group: dist.ProcessGroup,
) -> None:
    """
    Synchronize module states (i.e. parameters ``params`` and all not-yet-synced buffers) by broadcasting from rank 0 to all ranks.

    Precondition: ``sync_module_states == True`` and ``self.process_group`` has
    been set.
    """
    module_states: list[torch.Tensor] = []
    for buffer in module.buffers():
        # Avoid re-synchronizing buffers in case of nested wrapping
        if not getattr(buffer, FSDP_SYNCED, False):
            setattr(buffer, FSDP_SYNCED, True)
            detached_buffer = buffer.detach()
            if is_traceable_wrapper_subclass(detached_buffer):
                # NOTE: Here we assume no nested subclasses, at most one level of subclass
                # in both model's buffers and params
                attrs, _ = detached_buffer.__tensor_flatten__()  # type: ignore[attr-defined]
                for attr in attrs:
                    match getattr(detached_buffer, attr):
                        case torch.Tensor() as v:
                            module_states.append(v)
                        case OpaqueBase():
                            pass
                        case unexpected:
                            raise AssertionError(
                                f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                            )
            else:
                module_states.append(detached_buffer)

    for param in params:
        detached_param = param.detach()
        if is_traceable_wrapper_subclass(detached_param):
            attrs, _ = detached_param.__tensor_flatten__()  # type: ignore[attr-defined]
            for attr in attrs:
                match getattr(detached_param, attr):
                    case torch.Tensor() as v:
                        module_states.append(v)
                    case OpaqueBase():
                        pass
                    case unexpected:
                        raise AssertionError(
                            f"expected Tensor or OpaqueBase, got {type(unexpected)}"
                        )
        else:
            module_states.append(detached_param)

    _check_module_states_for_sync_module_states(module_states)
    _sync_params_and_buffers(
        process_group,
        module_states,
        PARAM_BROADCAST_BUCKET_SIZE,
        src=0,
    )