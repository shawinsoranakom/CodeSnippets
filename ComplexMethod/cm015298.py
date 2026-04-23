def param_search_greedy(x, bit_rate, n_bins=200, ratio=0.16):
    xmin, xmax = np.min(x), np.max(x)
    stepsize = (xmax - xmin) / np.float32(n_bins)
    min_bins = np.float32(n_bins) * (np.float32(1) - np.float32(ratio))
    xq, loss = _compress_uniform_simplified(x, bit_rate, xmin, xmax)

    solutions = []  # [(left, right, loss)] # local optima solution

    cur_min, cur_max, cur_loss = xmin, xmax, loss
    thr = min_bins * stepsize
    while cur_min + thr < cur_max:
        # move left
        xq, loss1 = _compress_uniform_simplified(
            x, bit_rate, cur_min + stepsize, cur_max
        )
        # move right
        xq, loss2 = _compress_uniform_simplified(
            x, bit_rate, cur_min, cur_max - stepsize
        )

        if cur_loss < loss1 and cur_loss < loss2:
            # found a local optima
            solutions.append((cur_min, cur_max, cur_loss))
        if loss1 < loss2:
            cur_min, cur_loss = cur_min + stepsize, loss1
        else:
            cur_max, cur_loss = cur_max - stepsize, loss2
    if solutions:
        best = solutions[0]
        for solution in solutions:
            if solution[-1] < best[-1]:
                best = solution
        return best[1], best[0]  # xmax, xmin
    return xmax, xmin