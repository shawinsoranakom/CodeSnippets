def get_optimal_checkpointing_policy_per_module(
    sac_stats: SACStats, memory_budget: float
) -> list[int]:
    """
    This is adapted from --
    https://github.com/facebookresearch/xformers/blob/c6c0ac31f1b08542a0bc27278c6ed10f825f6963/xformers/checkpoint.py#L375

    Given the SACStats of a module, including list of operators, their memory, runtimes, and metadata,
    decide via MILP an optimal set of operators to checkpoint under a given ``memory_budget``.

    Args:
        sac_stats: the SACStats object of the module
        memory_budget: a float between zero and one

    Returns:
        List[int]: the decision whether each operator should be saved (1) or recomptued (0).
    """
    if not (0 <= memory_budget <= 1):
        raise ValueError(
            f"`memory_budget` must be a float between 0 and 1. Got {memory_budget}."
        )
    num_ops = len(sac_stats.func_names)

    # Create a MILP problem
    prob = LpProblem("SAC-per-module", LpMaximize)

    # Create decision variables
    # x[i] = 1 means the i-th operator should be saved, otherwise it should be recomputed
    x = LpVariable.matrix("x", list(range(num_ops)), 0, 1, LpInteger)

    # Add constraints
    # [Constraint] random ops should be saved if ``force_store_random`` is True
    # otherwise, random ops should either be all recomputed or all saved
    if sac_stats.force_store_random:
        for i in sac_stats.rand_ops:
            prob += x[i] == SACDecision.SAVE.value
    else:
        for i1, i2 in zip(sac_stats.rand_ops[:-1], sac_stats.rand_ops[1:]):
            prob += x[i1] == x[i2]

    # [Constraint] view-like ops should always be recomputed
    for i in sac_stats.view_like_ops:
        prob += x[i] == SACDecision.RECOMPUTE.value

    # [Constraint] inplace ops should always be done in conjunction with its parent op
    for op, op_parent in sac_stats.inplace_ops:
        if op != op_parent:
            prob += x[op] == x[op_parent]
        else:
            prob += x[op] == SACDecision.SAVE.value

    # [Constraint] saved memory should be under the ``memory_budget``
    max_memory = math.ceil(memory_budget * sum(sac_stats.memory))
    prob += lpDot(x, sac_stats.memory) <= max_memory

    # [Objective] minimize recomputation time, note the ILP is a maximization problem
    # because x[i] == 1 means the op is saved (not recomputed), and thus recomputation
    # time is sum(sac_stats.runtimes) - lpDot(x, sac_stats.runtimes)
    prob += lpDot(x, sac_stats.runtimes)

    # Solve
    solver = PULP_CBC_CMD(gapRel=0.05, timeLimit=10, msg=0)
    status = prob.solve(solver)

    # If solver fails, print status and return empty solution
    if status != 1:
        logger.error("Solver failed to find a solution: %s", LpStatus[status])
        return []

    # Gather and return solution if optimal solution is found
    return [round(x[i].varValue) for i in range(num_ops)]