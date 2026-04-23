def easycache_forward_wrapper(executor, *args, **kwargs):
    # get values from args
    transformer_options: dict[str] = args[-1]
    if not isinstance(transformer_options, dict):
        transformer_options = kwargs.get("transformer_options")
        if not transformer_options:
            transformer_options = args[-2]
    easycache: EasyCacheHolder = transformer_options["easycache"]
    x, ax = _extract_tensor(args[0], easycache.output_channels)
    sigmas = transformer_options["sigmas"]
    uuids = transformer_options["uuids"]
    if sigmas is not None and easycache.is_past_end_timestep(sigmas):
        return executor(*args, **kwargs)
    # prepare next x_prev
    has_first_cond_uuid = easycache.has_first_cond_uuid(uuids)
    next_x_prev = x
    input_change = None
    do_easycache = easycache.should_do_easycache(sigmas)
    if do_easycache:
        easycache.check_metadata(x)
        # if there isn't a cache diff for current conds, we cannot skip this step
        can_apply_cache_diff = easycache.can_apply_cache_diff(uuids)
        # if first cond marked this step for skipping, skip it and use appropriate cached values
        if easycache.skip_current_step and can_apply_cache_diff:
            if easycache.verbose:
                logging.info(f"EasyCache [verbose] - was marked to skip this step by {easycache.first_cond_uuid}. Present uuids: {uuids}")
            result = easycache.apply_cache_diff(x, uuids)
            if ax is not None:
                result_audio = easycache.apply_cache_diff(ax, uuids, is_audio=True)
                return [result, result_audio]
            return result
        if easycache.initial_step:
            easycache.first_cond_uuid = uuids[0]
            has_first_cond_uuid = easycache.has_first_cond_uuid(uuids)
            easycache.initial_step = False
        if has_first_cond_uuid:
            if easycache.has_x_prev_subsampled():
                input_change = (easycache.subsample(x, uuids, clone=False) - easycache.x_prev_subsampled).flatten().abs().mean()
            if easycache.has_output_prev_norm() and easycache.has_relative_transformation_rate():
                approx_output_change_rate = (easycache.relative_transformation_rate * input_change) / easycache.output_prev_norm
                easycache.cumulative_change_rate += approx_output_change_rate
                if easycache.cumulative_change_rate < easycache.reuse_threshold and can_apply_cache_diff:
                    if easycache.verbose:
                        logging.info(f"EasyCache [verbose] - skipping step; cumulative_change_rate: {easycache.cumulative_change_rate}, reuse_threshold: {easycache.reuse_threshold}")
                    # other conds should also skip this step, and instead use their cached values
                    easycache.skip_current_step = True
                    result = easycache.apply_cache_diff(x, uuids)
                    if ax is not None:
                        result_audio = easycache.apply_cache_diff(ax, uuids, is_audio=True)
                        return [result, result_audio]
                    return result
                else:
                    if easycache.verbose:
                        logging.info(f"EasyCache [verbose] - NOT skipping step; cumulative_change_rate: {easycache.cumulative_change_rate}, reuse_threshold: {easycache.reuse_threshold}")
                    easycache.cumulative_change_rate = 0.0

    full_output: torch.Tensor = executor(*args, **kwargs)
    output, audio_output = _extract_tensor(full_output, easycache.output_channels)
    if has_first_cond_uuid and easycache.has_output_prev_norm():
        output_change = (easycache.subsample(output, uuids, clone=False) - easycache.output_prev_subsampled).flatten().abs().mean()
        if easycache.verbose:
            output_change_rate = output_change / easycache.output_prev_norm
            easycache.output_change_rates.append(output_change_rate.item())
        if easycache.has_relative_transformation_rate():
            approx_output_change_rate = (easycache.relative_transformation_rate * input_change) / easycache.output_prev_norm
            easycache.approx_output_change_rates.append(approx_output_change_rate.item())
            if easycache.verbose:
                logging.info(f"EasyCache [verbose] - approx_output_change_rate: {approx_output_change_rate}")
        if input_change is not None:
            easycache.relative_transformation_rate = output_change / input_change
        if easycache.verbose:
            logging.info(f"EasyCache [verbose] - output_change_rate: {output_change_rate}")
    # TODO: allow cache_diff to be offloaded
    easycache.update_cache_diff(output, next_x_prev, uuids)
    if audio_output is not None:
        easycache.update_cache_diff(audio_output, ax, uuids, is_audio=True)
    if has_first_cond_uuid:
        easycache.x_prev_subsampled = easycache.subsample(next_x_prev, uuids)
        easycache.output_prev_subsampled = easycache.subsample(output, uuids)
        easycache.output_prev_norm = output.flatten().abs().mean()
        if easycache.verbose:
            logging.info(f"EasyCache [verbose] - x_prev_subsampled: {easycache.x_prev_subsampled.shape}")
    return full_output