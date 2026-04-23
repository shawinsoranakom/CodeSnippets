def add_view_copy_derivatives(
    infos: dict[FunctionSchema, dict[str, DifferentiabilityInfo]],
    view_groups: list[NativeFunctionsViewGroup],
) -> None:
    # Get the map from each view op's name to its corresponding view group
    view_name_to_group: dict[OperatorName, NativeFunctionsViewGroup] = {
        g.view.func.name: g for g in view_groups
    }

    view_infos = {}

    for info_dispatch_dict in infos.values():
        # maybe_view_group only needs to be calculated once per info_dispatch_dict
        maybe_view_group = None
        view_copy_differentiability_infos = {}
        for dispatch_key, info in info_dispatch_dict.items():
            maybe_view_group = view_name_to_group.get(info.func.func.name, None)
            if maybe_view_group is not None and maybe_view_group.view_copy is not None:
                view_copy_info = info.create_view_copy_from_view_derivative(
                    maybe_view_group
                )
                if view_copy_info is not None:
                    fn_schema = view_copy_info.func.func
                    view_copy_differentiability_infos[dispatch_key] = view_copy_info
            else:
                break
        # prefer manually-defined derivatives if any
        # pyrefly: ignore [unbound-name]
        if len(view_copy_differentiability_infos) > 0 and fn_schema not in infos:
            if fn_schema is None:
                raise AssertionError("Expected fn_schema to be non-None")
            view_infos[fn_schema] = view_copy_differentiability_infos

    infos.update(view_infos)