def reconstruct_multicond_batch(c: MulticondLearnedConditioning, current_step):
    param = c.batch[0][0].schedules[0].cond

    tensors = []
    conds_list = []

    for composable_prompts in c.batch:
        conds_for_batch = []

        for composable_prompt in composable_prompts:
            target_index = 0
            for current, entry in enumerate(composable_prompt.schedules):
                if current_step <= entry.end_at_step:
                    target_index = current
                    break

            conds_for_batch.append((len(tensors), composable_prompt.weight))
            tensors.append(composable_prompt.schedules[target_index].cond)

        conds_list.append(conds_for_batch)

    if isinstance(tensors[0], dict):
        keys = list(tensors[0].keys())
        stacked = {k: stack_conds([x[k] for x in tensors]) for k in keys}
        stacked = DictWithShape(stacked, stacked['crossattn'].shape)
    else:
        stacked = stack_conds(tensors).to(device=param.device, dtype=param.dtype)

    return conds_list, stacked