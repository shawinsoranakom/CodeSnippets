def minimize(
    target_func,
    initial_parameters,
    reference_parameters,
    step_func,
    max_step=2,
    verbose=False,
    all_values=None,
):
    """Find a dict of parameters that minimizes the target function using
    the initial dict of parameters and a step function that progresses
    a specified parameter in a dict of parameters.

    Parameters
    ----------
    target_func (callable): a functional with the signature
      ``target_func(parameters: dict) -> float``
    initial_parameters (dict): a set of parameters used as an initial
      value to the minimization process.
    reference_parameters (dict): a set of parameters used as an
      reference value with respect to which the speed up is computed.
    step_func (callable): a functional with the signature
      ``step_func(parameter_name:str, parameter_value:int, direction:int, parameters:dict) -> int``
      that increments or decrements (when ``direction`` is positive or
      negative, respectively) the parameter with given name and value.
      When return value is equal to ``parameter_value``, it means that
      no step along the given direction can be made.

    Returns
    -------
    parameters (dict): a set of parameters that minimizes the target
      function.
    speedup_incr (float): a speedup change given in percentage.
    timing (float): the value of the target function at the parameters.
    sensitivity_message (str): a message containing sensitivity.
      information of parameters around the target function minimizer.
    """

    def to_key(parameters):
        return tuple(parameters[k] for k in sorted(parameters))

    def from_key(key, parameters):
        return dict(zip(sorted(parameters), key, strict=True))

    if all_values is None:
        all_values = {}

    directions = list(range(-max_step, max_step + 1))
    names = sorted(initial_parameters)
    all_directions = []
    for d_tuple in itertools.product(*((directions,) * len(names))):
        dist = sum(map(abs, d_tuple))
        if dist > 0 and dist <= max_step:
            all_directions.append((dist, d_tuple))
    all_directions.sort()

    try:
        reference_target = target_func(reference_parameters)
    except Exception as msg:
        if verbose and "out of resource" not in str(msg):
            print(f"{reference_parameters=} lead to failure: {msg}.")
        reference_target = None

    if reference_target is not None:
        all_values[to_key(reference_parameters)] = reference_target

    parameters = initial_parameters
    try:
        initial_target = target_func(parameters)
    except Exception as msg:
        if reference_target is None:
            if verbose:
                print(
                    f"{initial_parameters=} lead to failure: {msg}. Optimization failed!"
                )
            return {}, -1, -1, f"{msg}"
        if verbose and "out of resource" not in str(msg):
            print(
                f"{initial_parameters=} lead to failure: {msg}. Using reference parameters instead of initial parameters."
            )
        parameters = reference_parameters
        initial_target = reference_target

    if reference_target is None:
        if verbose:
            print("Using initial parameters instead of reference parameters.")
        reference_target = initial_target

    initial_key = to_key(parameters)
    minimal_target = all_values[initial_key] = initial_target
    pbar = tqdm(
        total=len(all_directions),
        desc="Tuning...",
        disable=not verbose,
        ncols=75,
    )
    while True:
        for i, (_, d_tuple) in enumerate(all_directions):
            pbar.update(1)
            next_parameters = parameters.copy()
            for name, direction in zip(names, d_tuple, strict=True):
                value = next_parameters[name]
                if direction == 0:
                    continue
                next_value = step_func(name, value, direction, parameters)
                if next_value == value:
                    break
                next_parameters[name] = next_value
            else:
                next_key = to_key(next_parameters)
                if next_key in all_values:
                    continue
                try:
                    next_target = target_func(next_parameters)
                except Exception as msg:
                    all_values[next_key] = str(msg)
                    if verbose and "out of resource" not in str(msg):
                        print(f"{next_parameters=} lead to failure: {msg}. Skipping.")
                    continue
                all_values[next_key] = next_target

                if next_target < minimal_target:
                    minimal_target = next_target
                    parameters = next_parameters
                    # pyrefly: ignore [unsupported-operation]
                    pbar.total += i + 1
                    break
        else:
            # ensure stable minimizer:
            minimizer_keys = {
                k
                for k, v in all_values.items()
                if isinstance(v, float) and abs(1 - v / minimal_target) < 0.001
            }
            minimizer_key = (
                initial_key if initial_key in minimizer_keys else min(minimizer_keys)
            )
            parameters = from_key(minimizer_key, parameters)
            speedup_incr = (1 - minimal_target / reference_target) * 100
            if speedup_incr < 0:
                if verbose:
                    print(
                        f"{speedup_incr=} is negative. Rerunning minimize with reference parameters as initial parameters."
                    )
                return minimize(
                    target_func,
                    reference_parameters,
                    reference_parameters,
                    step_func,
                    max_step=max_step,
                    verbose=verbose,
                    all_values=all_values,
                )
            sensitivity = []
            for name in parameters:
                value = parameters[name]
                rel_diffs = []
                for direction in range(-max_step, max_step + 1):
                    if direction == 0:
                        continue
                    next_value = step_func(name, value, direction, parameters)
                    if next_value == value:
                        rel_diffs.append(0)
                        continue
                    next_parameters = parameters.copy()
                    next_parameters[name] = next_value
                    next_key = to_key(next_parameters)
                    next_target = all_values.get(next_key)
                    if next_target is None or isinstance(next_target, str):
                        rel_diffs.append(0)
                        continue
                    rel_diff = (next_target / minimal_target - 1) * 100
                    rel_diffs.append(rel_diff)
                sensitivity.append((max(rel_diffs), rel_diffs, name))

            sensitivity_message = [f"timing0={initial_target:.3f}"]
            for _, rel_diffs, name in sorted(sensitivity, reverse=True):
                left_diffs = "|".join(
                    [f"{rel_diff:.1f}" for rel_diff in rel_diffs[:max_step]]
                )
                right_diffs = "|".join(
                    [f"{rel_diff:.1f}" for rel_diff in rel_diffs[max_step:]]
                )
                sensitivity_message.append(
                    f"{name}={parameters[name]} ({left_diffs}...{right_diffs} %)"
                )
            sensitivity_message = ", ".join(sensitivity_message)
            return parameters, speedup_incr, minimal_target, sensitivity_message