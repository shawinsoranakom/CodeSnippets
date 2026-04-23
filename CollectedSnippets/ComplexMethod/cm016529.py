def finalize_default_conds(model: 'BaseModel', hooked_to_run: dict[comfy.hooks.HookGroup,list[tuple[tuple,int]]], default_conds: list[list[dict]], x_in, timestep, model_options):
    # need to figure out remaining unmasked area for conds
    default_mults = []
    for _ in default_conds:
        default_mults.append(torch.ones_like(x_in))
    # look through each finalized cond in hooked_to_run for 'mult' and subtract it from each cond
    for lora_hooks, to_run in hooked_to_run.items():
        for cond_obj, i in to_run:
            # if no default_cond for cond_type, do nothing
            if len(default_conds[i]) == 0:
                continue
            area: list[int] = cond_obj.area
            if area is not None:
                curr_default_mult: torch.Tensor = default_mults[i]
                dims = len(area) // 2
                for i in range(dims):
                    curr_default_mult = curr_default_mult.narrow(i + 2, area[i + dims], area[i])
                curr_default_mult -= cond_obj.mult
            else:
                default_mults[i] -= cond_obj.mult
    # for each default_mult, ReLU to make negatives=0, and then check for any nonzeros
    for i, mult in enumerate(default_mults):
        # if no default_cond for cond type, do nothing
        if len(default_conds[i]) == 0:
            continue
        torch.nn.functional.relu(mult, inplace=True)
        # if mult is all zeros, then don't add default_cond
        if torch.max(mult) == 0.0:
            continue

        cond = default_conds[i]
        for x in cond:
            # do get_area_and_mult to get all the expected values
            p = get_area_and_mult(x, x_in, timestep)
            if p is None:
                continue
            # replace p's mult with calculated mult
            p = p._replace(mult=mult)
            if p.hooks is not None:
                model.current_patcher.prepare_hook_patches_current_keyframe(timestep, p.hooks, model_options)
            hooked_to_run.setdefault(p.hooks, list())
            hooked_to_run[p.hooks] += [(p, i)]