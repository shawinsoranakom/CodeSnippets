def redistribute_local_args(
        op_info: OpInfo,
        suggested_input_schema: OpSchema,
        use_val_from_redistribute_schema: bool,
    ) -> None:
        debug_mode = get_active_debug_mode()

        # NOTE: it's very rare that we need to reshard kwargs so we intentionally skip it
        if op_info.args_tree_spec is not None:
            flatten_args_schema_to_reshard = tuple(
                pytree.tree_leaves(suggested_input_schema.args_schema)
            )
        else:
            flatten_args_schema_to_reshard = suggested_input_schema.args_schema

        new_local_args: list[object] = []
        for i, arg_spec in enumerate(op_info.flat_args_schema):
            reshard_arg_spec = flatten_args_schema_to_reshard[i]
            if isinstance(arg_spec, DTensorSpec):
                local_tensor = cast(torch.Tensor, op_info.local_args[i])
                if arg_spec != reshard_arg_spec:
                    redistribute_context = (
                        debug_mode.record_redistribute_calls(  # type: ignore[union-attr]
                            i, arg_spec, reshard_arg_spec
                        )
                        if debug_mode is not None
                        else contextlib.nullcontext()
                    )

                    ExplicitRedistributionContext.observe_redistribution(
                        arg_spec,
                        # pyrefly: ignore [bad-argument-type]
                        reshard_arg_spec,
                        LazyString(
                            _format_implicit_redistribution_msg,
                            op_info.schema or suggested_input_schema.op,
                        ),
                    )
                    with redistribute_context:
                        resharded_local_tensor = redistribute_local_tensor(
                            local_tensor,
                            arg_spec,
                            # pyrefly: ignore [bad-argument-type]
                            reshard_arg_spec,
                        )
                    new_local_args.append(resharded_local_tensor)
                else:
                    new_local_args.append(local_tensor)
            else:
                if use_val_from_redistribute_schema:
                    # args can be updated for view related ops, we refer to the
                    # update in redistribute_schema.
                    new_local_args.append(reshard_arg_spec)
                else:
                    new_local_args.append(arg_spec)

        # Append extra non-tensor args from rewritten schema (e.g., dims tuple).
        if use_val_from_redistribute_schema:
            for i in range(
                len(op_info.flat_args_schema), len(flatten_args_schema_to_reshard)
            ):
                new_local_args.append(flatten_args_schema_to_reshard[i])

        op_info.local_args = tuple(new_local_args)