def timed(
    model,
    model_iter_fn,
    example_inputs,
    times=1,
    return_result=False,
    collect_outputs=False,
    batch_size=None,
):
    use_xla = tensor_is_on_xla(example_inputs)
    synchronize()

    if batch_size:
        patch_torch_manual_seed()

    if use_xla:
        xm.mark_step()
        xm.wait_device_ops()

    def vary_batch(t: torch.Tensor, new_batch_size) -> torch.Tensor:
        for i, s in enumerate(t.size()):
            if s == batch_size:
                # If new batch is smaller, we truncate
                if new_batch_size < batch_size:
                    indexer = [slice(None)] * t.ndim
                    indexer[i] = slice(0, new_batch_size)
                    t = t[tuple(indexer)]
                # If new batch is greater, we just duplicate the last row
                # over and over until we hit the desired batch size
                elif new_batch_size > batch_size:
                    indexer = [slice(None)] * t.ndim
                    indexer[i] = -1
                    last_slice = t[tuple(indexer)].unsqueeze(i)
                    repeat_shape = list(t.shape)
                    repeat_shape[i] = new_batch_size - batch_size
                    padding = last_slice.expand(*repeat_shape)
                    t = torch.cat([t, padding], dim=i)
                break
        return t

    time_total = 0
    # Dont collect outputs to correctly measure timing
    for i in range(times):
        # If batch_size is 1, it too often collides with other non batch size
        # dimensions resulting in errors.
        if batch_size and batch_size > 1:
            # Calculate new batch size by varying the original batch size by up to 20%
            # Ensure it's at least greater than 1
            variation = random.uniform(0.8, 1.2)
            new_batch_size = max(2, int(batch_size * variation))
            example_inputs = tree_map_only(
                torch.Tensor, lambda x: vary_batch(x, new_batch_size), example_inputs
            )
        # Put this call inside the loop to reset the seed for each iteration.
        # Don't include reset_rng_state() to correctly measure timing
        reset_rng_state(use_xla)
        t_iter_begin = time.perf_counter()
        result = model_iter_fn(model, example_inputs, collect_outputs=collect_outputs)

        # instead of calling sync on result_list, we should call mark_step.
        # In training case, result_list may be empty, but we want to
        # send all the pending graphs for compilation.
        if use_xla:
            # For the model running on regular torchxla (baseline), we need the
            # mark step to send the accumulated graph for compilation.
            #
            # For the model running with dynamo/torchxla bridge, in training case,
            # we need the mark step to send the optimizer graph out for
            # compilation.
            xm.mark_step()
        t_iter_end = time.perf_counter()
        time_total += t_iter_end - t_iter_begin

    t_0 = time.perf_counter()
    if use_xla:
        xm.wait_device_ops()
    synchronize()
    t_1 = time.perf_counter()
    time_total += t_1 - t_0
    return (time_total, result) if return_result else time_total