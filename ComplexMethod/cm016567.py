def combine_all_hooks(hooks_list: list[HookGroup], require_count=0) -> HookGroup:
        actual: list[HookGroup] = []
        for group in hooks_list:
            if group is not None:
                actual.append(group)
        if len(actual) < require_count:
            raise Exception(f"Need at least {require_count} hooks to combine, but only had {len(actual)}.")
        # if no hooks, then return None
        if len(actual) == 0:
            return None
        # if only 1 hook, just return itself without cloning
        elif len(actual) == 1:
            return actual[0]
        final_hook: HookGroup = None
        for hook in actual:
            if final_hook is None:
                final_hook = hook.clone()
            else:
                final_hook = final_hook.clone_and_combine(hook)
        return final_hook