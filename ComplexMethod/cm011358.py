def recurse(module: nn.Module, curr_fqn: str) -> Generator:
        visited_modules.add(module)

        curr_fqn = f"{curr_fqn}." if curr_fqn else ""
        for name, submodule in module.named_children():
            if submodule in visited_modules:
                continue
            # if user have state_dict_hooks in their model, they can add the state_dict key changes
            # at dsd_fqn_modifiers in input to align with the function of state_dict_hook
            if (
                hasattr(module, dsd_fqn_modifiers)
                and name in getattr(module, dsd_fqn_modifiers)().values()
            ):
                # skip _fqn_modifiers here thus remove the last `.` added
                new_fqn = curr_fqn[:-1]
            else:
                new_fqn = f"{curr_fqn}{name}"
            yield from recurse(submodule, new_fqn)

        for name, obj in chain(
            module.named_buffers(recurse=False), module.named_parameters(recurse=False)
        ):
            if name in module._non_persistent_buffers_set:
                continue
            new_fqn = f"{curr_fqn}{name}"
            yield new_fqn, obj

        if (
            getattr(module.__class__, "get_extra_state", nn.Module.get_extra_state)
            != nn.Module.get_extra_state
        ):
            new_fqn = f"{curr_fqn}{nn.modules.module._EXTRA_STATE_KEY_SUFFIX}"
            yield new_fqn, _EXTRA_STATE()