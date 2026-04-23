def get_hooks_from_cond(cond, full_hooks: comfy.hooks.HookGroup):
    # get hooks from conds, and collect cnets so they can be checked for extra_hooks
    cnets: list[ControlBase] = []
    for c in cond:
        if 'hooks' in c:
            for hook in c['hooks'].hooks:
                full_hooks.add(hook)
        if 'control' in c:
            cnets.append(c['control'])

    def get_extra_hooks_from_cnet(cnet: ControlBase, _list: list):
        if cnet.extra_hooks is not None:
            _list.append(cnet.extra_hooks)
        if cnet.previous_controlnet is None:
            return _list
        return get_extra_hooks_from_cnet(cnet.previous_controlnet, _list)

    hooks_list = []
    cnets = set(cnets)
    for base_cnet in cnets:
        get_extra_hooks_from_cnet(base_cnet, hooks_list)
    extra_hooks = comfy.hooks.HookGroup.combine_all_hooks(hooks_list)
    if extra_hooks is not None:
        for hook in extra_hooks.hooks:
            full_hooks.add(hook)

    return full_hooks