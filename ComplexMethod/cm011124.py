def module_fn(
        module, prefix, tree_level, sharded_tree_info, sharded_module_name_to_fqns
    ):
        num_spaces = tree_level * 4
        trimed_prefix = (
            prefix[:-1] if (len(prefix) > 0 and prefix[-1] == ".") else prefix
        )
        prefixed_module_name = trimed_prefix + "[" + module.__class__.__name__ + "]"
        printed_prefixed_module_name = " " * num_spaces + prefixed_module_name

        state = _get_module_fsdp_state(module)
        if state is None:
            sharded_tree_info[0] += printed_prefixed_module_name + "\n"
            return

        handle = state._fully_sharded_module_to_handle.get(module, None)

        if handle:
            sharded_tree_info[0] += (
                printed_prefixed_module_name + " FULLY SHARDED" + "\n"
            )
        else:
            sharded_tree_info[0] += printed_prefixed_module_name + "\n"

        if handle:
            param = handle.flat_param
            if not isinstance(param, flat_param_file.FlatParameter):
                raise AssertionError(f"Expected FlatParameter, got {type(param)}")
            global_fqns = [
                clean_tensor_name(prefix + name) for name in param._fqns
            ]  # prefixed from the top level `model` (i.e. including `prefix`)

            if prefixed_module_name in sharded_module_name_to_fqns:
                sharded_module_name_to_fqns[prefixed_module_name].extend(global_fqns)
            else:
                sharded_module_name_to_fqns[prefixed_module_name] = global_fqns