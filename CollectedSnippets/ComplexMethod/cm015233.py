def get_bdim_choices_batch_norm(
    num_tensors, _, running_mean=None, running_var=None, *args
):
    choices = []
    options = (-1, None)

    # instance norm turns these into unbatched 0 tensors, so we cannot batch the input if either is not specified
    if running_mean is None or running_var is None:
        choices.append((None,) + (0,) * (num_tensors - 1))
        for choice in itertools.product(options, repeat=num_tensors - 1):
            choices.append((None,) + choice)

    else:
        # running_mean and running_var are specified as tensors. Batch norm doesn't work if the input is batched but
        # running_mean/var are unbatched, so this tests all other cases
        choices.append((0,) * num_tensors)
        for choice in itertools.product(options, repeat=num_tensors):
            input_bdim = choice[0]
            running_mean_bdim = choice[1]
            running_var_bdim = choice[2]
            if input_bdim and (not running_mean_bdim or not running_var_bdim):
                continue
            choices.append(choice)

    if choices[-1] != (None,) * num_tensors:
        raise AssertionError(
            f"Expected choices[-1] to be {(None,) * num_tensors}, got {choices[-1]}"
        )
    return tuple(choices[:-1])