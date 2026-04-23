def lazycache_predict_noise_wrapper(executor, *args, **kwargs):
    # get values from args
    timestep: float = args[1]
    model_options: dict[str] = args[2]
    easycache: LazyCacheHolder = model_options["transformer_options"]["easycache"]
    if easycache.is_past_end_timestep(timestep):
        return executor(*args, **kwargs)
    x: torch.Tensor = args[0][:, :easycache.output_channels]
    # prepare next x_prev
    next_x_prev = x
    input_change = None
    do_easycache = easycache.should_do_easycache(timestep)
    if do_easycache:
        easycache.check_metadata(x)
        if easycache.has_x_prev_subsampled():
            if easycache.has_x_prev_subsampled():
                input_change = (easycache.subsample(x, clone=False) - easycache.x_prev_subsampled).flatten().abs().mean()
            if easycache.has_output_prev_norm() and easycache.has_relative_transformation_rate():
                approx_output_change_rate = (easycache.relative_transformation_rate * input_change) / easycache.output_prev_norm
                easycache.cumulative_change_rate += approx_output_change_rate
                if easycache.cumulative_change_rate < easycache.reuse_threshold:
                    if easycache.verbose:
                        logging.info(f"LazyCache [verbose] - skipping step; cumulative_change_rate: {easycache.cumulative_change_rate}, reuse_threshold: {easycache.reuse_threshold}")
                    # other conds should also skip this step, and instead use their cached values
                    easycache.skip_current_step = True
                    return easycache.apply_cache_diff(x)
                else:
                    if easycache.verbose:
                        logging.info(f"LazyCache [verbose] - NOT skipping step; cumulative_change_rate: {easycache.cumulative_change_rate}, reuse_threshold: {easycache.reuse_threshold}")
                    easycache.cumulative_change_rate = 0.0
    output: torch.Tensor = executor(*args, **kwargs)
    if easycache.has_output_prev_norm():
        output_change = (easycache.subsample(output, clone=False) - easycache.output_prev_subsampled).flatten().abs().mean()
        if easycache.verbose:
            output_change_rate = output_change / easycache.output_prev_norm
            easycache.output_change_rates.append(output_change_rate.item())
        if easycache.has_relative_transformation_rate():
            approx_output_change_rate = (easycache.relative_transformation_rate * input_change) / easycache.output_prev_norm
            easycache.approx_output_change_rates.append(approx_output_change_rate.item())
            if easycache.verbose:
                logging.info(f"LazyCache [verbose] - approx_output_change_rate: {approx_output_change_rate}")
        if input_change is not None:
            easycache.relative_transformation_rate = output_change / input_change
        if easycache.verbose:
            logging.info(f"LazyCache [verbose] - output_change_rate: {output_change_rate}")
    # TODO: allow cache_diff to be offloaded
    easycache.update_cache_diff(output, next_x_prev)
    easycache.x_prev_subsampled = easycache.subsample(next_x_prev)
    easycache.output_prev_subsampled = easycache.subsample(output)
    easycache.output_prev_norm = output.flatten().abs().mean()
    if easycache.verbose:
        logging.info(f"LazyCache [verbose] - x_prev_subsampled: {easycache.x_prev_subsampled.shape}")
    return output