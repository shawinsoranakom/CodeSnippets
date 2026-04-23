def _resolve_group(
    group: RANK_TYPES, tag: str = ""
) -> dist.ProcessGroup | c10d.GroupName:
    """
    Given group in RANK_TYPES, return a ProcessGroup or group name.
    """
    # `tag` will be deprecated. See details in:
    # https://github.com/pytorch/pytorch/issues/93173#issuecomment-1907095208
    if isinstance(group, dist.ProcessGroup):
        return group
    elif isinstance(group, str):
        # In some cases Dynamo doesn't like tracing through NewType constructors
        # - so use a cast instead (the actual newtype representation is
        # literally the underlying type so this is fine). I haven't been able to
        # reproduce it in isolation (see T247631668).
        # pyrefly: ignore [redundant-cast]
        group_name = cast(c10d.GroupName, group)  # c10d.GroupName(group)
        return group_name
    elif isinstance(group, DeviceMesh):
        if group.ndim != 1:
            raise AssertionError(
                "Only 1D mesh is supported, pass in (DeviceMesh, int) together if mesh > 1D"
            )
        if dist.config.compile_on_one_rank:
            return torch.ops._dtensor.mesh_get_process_group(group, 0)
        return group._dim_group_names[0]
    elif isinstance(group, tuple):
        if (
            len(group) == 2
            and isinstance(group[0], DeviceMesh)
            and isinstance(group[1], int)
        ):
            dmesh = group[0]
            dim = group[1]
            if dist.config.compile_on_one_rank:
                return torch.ops._dtensor.mesh_get_process_group(dmesh, dim)
            return dmesh._dim_group_names[dim]
        else:
            raise ValueError(
                f"Invalid tuple for group must be (DeviceMesh, int). Instead got {(type(group[0]), type(group[1]))}"
            )
    elif isinstance(group, list):
        if not is_torchdynamo_compiling():
            warnings.warn(
                "The combination of ranks + tag as process group "
                "identifier has been deprecated. Please switch to "
                "using ProcessGroup, DeviceMesh, or group name instead.",
                FutureWarning,
                stacklevel=3,
            )
        return c10d._resolve_group_name_by_ranks_and_tag(
            # pyrefly: ignore [redundant-cast]
            cast(list[int], group),
            tag,
        )
    else:
        raise ValueError(f"Unsupported group type: {type(group)}, {group}")