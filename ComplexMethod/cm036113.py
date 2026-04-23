def _generate_fake_step_update(
    persistent_batch: list[LogitsProcsRequestParams],
    workload_params: list[LogitsProcsRequestParams],
    wdx: int,
    batch_update_builder: BatchUpdateBuilder,
) -> tuple[BatchUpdate | None, int, int]:
    batch_size = len(persistent_batch)
    workload_size = len(workload_params)
    workload_reqs_remaining = workload_size - wdx
    max_add_remove_per_step = max(1, int(0.2 * workload_size))

    # 50% of steps: add no reqs
    # Other 50%: add a limited number of reqs (less than the number
    # of workload reqs remaining, less than an arbitrary max)
    # If no workload reqs remain: 100% of steps have 0 adds
    num_step_add = (
        random.choice(
            [
                0,
                random.randint(
                    1, min(max_add_remove_per_step, workload_reqs_remaining)
                ),
            ]
        )
        if workload_reqs_remaining
        else 0
    )

    # 50% of steps: remove no requests
    # Other 50%: remove a limited number of reqs (less than the number
    # persistent batch reqs remaining, less than an arbitrary max)
    # If persistent batch is empty: 100% of steps have 0 removals until
    # more requests are added. Assume that removed requests are always
    # drawn from the current batch, before new adds
    num_step_remove = (
        random.choice([0, random.randint(1, min(max_add_remove_per_step, batch_size))])
        if batch_size
        else 0
    )

    num_step_add_replace = min(num_step_add, num_step_remove)

    # Generate fake removed request indices drawn from persistent batch indices
    for removal in random.sample(range(batch_size), num_step_remove):
        batch_update_builder.removed_append(removal)

    # Get added requests from workload
    for add_req_params in workload_params[wdx : (wdx + num_step_add_replace)]:
        # Replace as many removed requests as possible with added requests
        add_remove_idx = batch_update_builder.pop_removed()
        batch_update_builder.added.append(
            (
                add_remove_idx,
                add_req_params.params,
                add_req_params.prompt_tokens,
                add_req_params.out_tokens,
            )
        )
        persistent_batch[add_remove_idx] = add_req_params

    # Append remaining added requests to end of batch
    add_reqs_append = workload_params[
        (wdx + num_step_add_replace) : (wdx + num_step_add)
    ]
    batch_update_builder.added.extend(
        [
            (
                adx + batch_size,
                add_req_params.params,
                add_req_params.prompt_tokens,
                add_req_params.out_tokens,
            )
            for adx, add_req_params in enumerate(add_reqs_append)
        ]
    )
    persistent_batch.extend(add_reqs_append)
    pre_condense_batch_size = len(persistent_batch)
    wdx += num_step_add  # Update workload offset

    # Simulate condensing persistent batch
    last_nonempty_index = pre_condense_batch_size - 1
    condensed_to_idxs = set()
    while batch_update_builder.removed:
        if (
            last_nonempty_index in batch_update_builder.removed
            or last_nonempty_index in condensed_to_idxs
        ):
            last_nonempty_index -= 1
            continue
        # last_nonempty_index is the highest persistent batch index that was
        # not removed
        first_empty_index = batch_update_builder.peek_removed()
        assert first_empty_index is not None
        if first_empty_index > last_nonempty_index:
            break
        # first_empty_index is the lowest removed persistent batch index
        # that is less than last_nonempty_index
        #
        # move last_nonempty_index -> first_empty_index
        batch_update_builder.pop_removed()
        condensed_to_idxs.add(first_empty_index)
        persistent_batch[first_empty_index] = persistent_batch[last_nonempty_index]
        batch_update_builder.moved.append(
            (last_nonempty_index, first_empty_index, MoveDirectionality.UNIDIRECTIONAL)
        )

        last_nonempty_index -= 1

    # Now removed requests & gaps left by non-removed requests that got
    # moved downward are grouped consecutively in the upper indices of
    # the persistent batch. Truncate them to get condensed persistent batch
    condensed_batch_size = batch_size + num_step_add - num_step_remove
    persistent_batch[:] = persistent_batch[0:condensed_batch_size]

    if condensed_batch_size > 1:
        # Simulate arbitrary batch ordering in the kernel backend
        # Generate a random number k of non-overlapping swap tuples
        k = random.randint(0, condensed_batch_size // 2)
        idxs = list(range(condensed_batch_size))
        random.shuffle(idxs)
        swaps = [tuple(sorted([idxs[2 * i], idxs[2 * i + 1]])) for i in range(k)]
        batch_update_builder.moved.extend(
            [(sw[0], sw[1], MoveDirectionality.SWAP) for sw in swaps]
        )
        for adx, bdx in swaps:
            persistent_batch[adx], persistent_batch[bdx] = (
                persistent_batch[bdx],
                persistent_batch[adx],
            )

    return (
        batch_update_builder.get_and_reset(condensed_batch_size),
        wdx,
        workload_size - wdx,
    )