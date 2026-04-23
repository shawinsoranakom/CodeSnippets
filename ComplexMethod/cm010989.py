def _get_split_source(pg: ProcessGroup):
    split_from = None
    if pg.bound_device_id:
        split_from = pg._get_backend(pg.bound_device_id)
    elif pg is _world.default_pg:
        try:
            split_from = pg._get_backend(torch.device("cuda"))
        except RuntimeError:
            # no cuda device associated with this backend
            pass

    if not split_from or not split_from.supports_splitting:
        return None

    # If necessary, find a backend to split from by peeling process
    # group wrappers from our potentially wrapped process group.
    while _GLOO_AVAILABLE and isinstance(split_from, _ProcessGroupWrapper):
        split_from = split_from.wrapped_pg

    return split_from