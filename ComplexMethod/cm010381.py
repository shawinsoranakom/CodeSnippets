def _generate_new_op_kwargs_from_bases(
    schema, kwargs, all_bases, _only_clone_these_bases, _is_out
):
    mutable_args_names, mutable_args_types = get_mutable_args_from_schema(schema)

    if _is_out:
        # For out= ops, _all_bases is empty. Create empty tensors from the
        # metadata that was encoded by _do_auto_functionalize_v2_for_out_operator.
        new_kwargs = dict(**kwargs)
        created_out_tensors = []
        for arg_name in mutable_args_names:
            size = new_kwargs.pop(f"_{arg_name}_size")
            stride = new_kwargs.pop(f"_{arg_name}_stride")
            dtype = new_kwargs.pop(f"_{arg_name}_dtype")
            device = new_kwargs.pop(f"_{arg_name}_device")
            t = torch.empty_strided(size, stride, dtype=dtype, device=device)
            new_kwargs[arg_name] = t
            created_out_tensors.append(t)
        return new_kwargs, created_out_tensors

    args_view_info = read_view_information_from_args(
        mutable_args_names, mutable_args_types, kwargs, all_bases
    )

    def maybe_copy(i, t):
        if t is None:
            return None
        if i in _only_clone_these_bases:
            return clone_preserve_strides(t)
        else:
            return t

    all_bases_new = [maybe_copy(i, t) for i, t in enumerate(all_bases)]

    # create new args
    new_kwargs = dict(**kwargs)

    # re-generate all inputs from all_bases_new using args_view_info and add them to new_kwargs.
    for arg_name in mutable_args_names:
        if args_view_info[arg_name] is None:
            new_kwargs[arg_name] = None
        elif isinstance(args_view_info[arg_name], list):
            new_kwargs[arg_name] = []
            for i, elem in enumerate(args_view_info[arg_name]):
                if elem is None:
                    new_kwargs[arg_name].append(None)
                else:
                    view_info = args_view_info[arg_name][i]
                    new_kwargs[arg_name].append(
                        view_info.regenerate_view(all_bases_new)
                    )
        else:
            new_kwargs[arg_name] = args_view_info[arg_name].regenerate_view(
                all_bases_new
            )

    return new_kwargs, all_bases_new