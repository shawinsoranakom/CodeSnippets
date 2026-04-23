def f(module: torch.nn.Module, prefix: str, tree_level: int, *args, **kwargs):
        # Call the module function before recursing over children (pre-order)
        module_fn(module, prefix, tree_level, *args, **kwargs)
        for submodule_name, submodule in module.named_children():
            if submodule is None:
                continue
            new_prefix = prefix + submodule_name + "."
            new_tree_level = tree_level + 1
            if filter_prefixes is not None:
                if new_prefix not in filter_prefixes:
                    # DMP's named_parameter() will mess up the traversal with
                    # ``named_children`` + `named_parameter(recurse=False)``.
                    # This hack is a must to make the traversal work.
                    # TODO: Remove this hack once DMP + FSDP is not supported.
                    # It turns out that recursive wrapping may trigger this as
                    # well.
                    if (
                        submodule_name == "_fsdp_wrapped_module"
                        or submodule_name == "_dmp_wrapped_module"
                    ):
                        new_prefix = prefix
                    elif submodule_name == "module":
                        new_prefix = prefix
            f(submodule, new_prefix, new_tree_level, *args, **kwargs)