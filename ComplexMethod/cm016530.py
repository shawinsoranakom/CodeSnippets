def _calc_cond_batch(model: BaseModel, conds: list[list[dict]], x_in: torch.Tensor, timestep, model_options):
    out_conds = []
    out_counts = []
    # separate conds by matching hooks
    hooked_to_run: dict[comfy.hooks.HookGroup,list[tuple[tuple,int]]] = {}
    default_conds = []
    has_default_conds = False

    for i in range(len(conds)):
        out_conds.append(torch.zeros_like(x_in))
        out_counts.append(torch.ones_like(x_in) * 1e-37)

        cond = conds[i]
        default_c = []
        if cond is not None:
            for x in cond:
                if 'default' in x:
                    default_c.append(x)
                    has_default_conds = True
                    continue
                p = get_area_and_mult(x, x_in, timestep)
                if p is None:
                    continue
                if p.hooks is not None:
                    model.current_patcher.prepare_hook_patches_current_keyframe(timestep, p.hooks, model_options)
                hooked_to_run.setdefault(p.hooks, list())
                hooked_to_run[p.hooks] += [(p, i)]
        default_conds.append(default_c)

    if has_default_conds:
        finalize_default_conds(model, hooked_to_run, default_conds, x_in, timestep, model_options)

    model.current_patcher.prepare_state(timestep)

    # run every hooked_to_run separately
    for hooks, to_run in hooked_to_run.items():
        while len(to_run) > 0:
            first = to_run[0]
            first_shape = first[0][0].shape
            to_batch_temp = []
            for x in range(len(to_run)):
                if can_concat_cond(to_run[x][0], first[0]):
                    to_batch_temp += [x]

            to_batch_temp.reverse()
            to_batch = to_batch_temp[:1]

            free_memory = model.current_patcher.get_free_memory(x_in.device)
            for i in range(1, len(to_batch_temp) + 1):
                batch_amount = to_batch_temp[:len(to_batch_temp)//i]
                input_shape = [len(batch_amount) * first_shape[0]] + list(first_shape)[1:]
                cond_shapes = collections.defaultdict(list)
                for tt in batch_amount:
                    cond = {k: v.size() for k, v in to_run[tt][0].conditioning.items()}
                    for k, v in to_run[tt][0].conditioning.items():
                        cond_shapes[k].append(v.size())

                if model.memory_required(input_shape, cond_shapes=cond_shapes) * 1.5 < free_memory:
                    to_batch = batch_amount
                    break

            input_x = []
            mult = []
            c = []
            cond_or_uncond = []
            uuids = []
            area = []
            control = None
            patches = None
            for x in to_batch:
                o = to_run.pop(x)
                p = o[0]
                input_x.append(p.input_x)
                mult.append(p.mult)
                c.append(p.conditioning)
                area.append(p.area)
                cond_or_uncond.append(o[1])
                uuids.append(p.uuid)
                control = p.control
                patches = p.patches

            batch_chunks = len(cond_or_uncond)
            input_x = torch.cat(input_x)
            c = cond_cat(c)
            timestep_ = torch.cat([timestep] * batch_chunks)

            transformer_options = model.current_patcher.apply_hooks(hooks=hooks)
            if 'transformer_options' in model_options:
                transformer_options = comfy.patcher_extension.merge_nested_dicts(transformer_options,
                                                                                 model_options['transformer_options'],
                                                                                 copy_dict1=False)

            if patches is not None:
                transformer_options["patches"] = comfy.patcher_extension.merge_nested_dicts(
                    transformer_options.get("patches", {}),
                    patches
                )

            transformer_options["cond_or_uncond"] = cond_or_uncond[:]
            transformer_options["uuids"] = uuids[:]
            transformer_options["sigmas"] = timestep

            c['transformer_options'] = transformer_options

            if control is not None:
                c['control'] = control.get_control(input_x, timestep_, c, len(cond_or_uncond), transformer_options)

            if 'model_function_wrapper' in model_options:
                output = model_options['model_function_wrapper'](model.apply_model, {"input": input_x, "timestep": timestep_, "c": c, "cond_or_uncond": cond_or_uncond}).chunk(batch_chunks)
            else:
                output = model.apply_model(input_x, timestep_, **c).chunk(batch_chunks)

            for o in range(batch_chunks):
                cond_index = cond_or_uncond[o]
                a = area[o]
                if a is None:
                    out_conds[cond_index] += output[o] * mult[o]
                    out_counts[cond_index] += mult[o]
                else:
                    out_c = out_conds[cond_index]
                    out_cts = out_counts[cond_index]
                    dims = len(a) // 2
                    for i in range(dims):
                        out_c = out_c.narrow(i + 2, a[i + dims], a[i])
                        out_cts = out_cts.narrow(i + 2, a[i + dims], a[i])
                    out_c += output[o] * mult[o]
                    out_cts += mult[o]

    for i in range(len(out_conds)):
        out_conds[i] /= out_counts[i]

    return out_conds