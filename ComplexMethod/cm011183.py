def _get_sac_tradeoff_pwlf_stats(
        self,
        sac_stats: SACStats,
        greedy_order_meta: SACGreedyOrderMeta,
        n_segments: int = 2,
        save_tradeoff_graph: bool = False,
        filename: str = "ac_tradeoff",
    ) -> SACTradeOffStats:
        try:
            import numpy as np  # type: ignore[import-not-found]
            import pwlf  # type: ignore[import-untyped, import-not-found]
        except ImportError as err:
            raise ImportError("Please install pwlf and numpy package.") from err

        stored_ops, recomputed_ops, inplace_op_groups, random_ops_group, msps_meta = (
            greedy_order_meta.stored_ops,
            greedy_order_meta.recomputed_ops,
            greedy_order_meta.inplace_op_groups,
            greedy_order_meta.random_ops_group,
            greedy_order_meta.msps_meta,
        )
        # 1. Initialize the discarded memory and recomputation runtime to sum of already chosen recomputed_ops
        recomp_indices: set[int] = set()
        for r_idx in recomputed_ops:
            recomp_indices.add(r_idx)
            if r_idx in inplace_op_groups:
                recomp_indices.update(inplace_op_groups[r_idx])
            if r_idx in random_ops_group:
                recomp_indices.update(random_ops_group[r_idx])

        discarded_mem = sum(sac_stats.memory[op_idx] for op_idx in recomp_indices)
        recomp_runtime = sum(sac_stats.runtimes[op_idx] for op_idx in recomp_indices)
        # 2. Initialize the max recomputation time and total recomputation memory
        sac_runtime = sum(sac_stats.runtimes)
        sac_memory = sum(sac_stats.memory)
        # 3. Tradeoff curve stores the KV pair of the discarded memory to total memory and,
        # recomputation time to total runtime incurred.
        delta = 1e-2
        tradeoff_curve = OrderedDict()
        # 4. Initialize the trade-off curve with the stats of of already chosen recomputed_ops
        tradeoff_curve[(discarded_mem / sac_memory) + delta] = (
            recomp_runtime / sac_runtime
        )
        # 5. Update the trade-off curve with memory and runtime stats of SAC candidates in the
        # greedy order of their ``MSPS``.
        for cand in msps_meta:
            discarded_mem += cand.memory
            recomp_runtime += cand.runtime
            tradeoff_curve[(discarded_mem / sac_memory) + delta] = (
                recomp_runtime / sac_runtime
            )
        # 6. Finally, we add the memory and recomputation time of the always stored ops.
        stored_indices: set[int] = set()
        for s_idx in stored_ops:
            stored_indices.add(s_idx)
            if s_idx in inplace_op_groups:
                stored_indices.update(inplace_op_groups[s_idx])
            if s_idx in random_ops_group:
                stored_indices.update(random_ops_group[s_idx])
        discarded_mem += sum(sac_stats.memory[op_idx] for op_idx in stored_indices)
        recomp_runtime += sum(sac_stats.runtimes[op_idx] for op_idx in stored_indices)
        tradeoff_curve[(discarded_mem / sac_memory) + delta] = (
            recomp_runtime / sac_runtime
        )
        x_ = list(tradeoff_curve.keys())
        y_ = list(tradeoff_curve.values())
        # 7. We shift the y values to left and x values to right to upperbound the trade-off function
        # TODO: Write a better explanation why this needs to be done
        x = x_[: len(x_) - 1]
        y = y_[1:]
        tradeoff_pwlf = pwlf.PiecewiseLinFit(x, y)
        # 8. Fit a piecewise linear function with the specified number of segments to the trade-off curve.
        n_segments = max(min(len(x) - 2, n_segments), 1)
        tradeoff_pwlf.fit(n_segments=n_segments)

        # save prediction graph
        def save_prediction_graph(
            pwlf_: pwlf.PiecewiseLinFit, x: list[float], y: list[float], filename: str
        ) -> None:
            try:
                import matplotlib.pyplot as plt  # type: ignore[import-not-found]
                import numpy as np  # type: ignore[import-not-found]
            except ImportError as err:
                raise ImportError(
                    "Install matplotlib and numpy using pip: pip install matplotlib numpy"
                ) from err
            # predict for the determined points
            xHat = np.linspace(min(x), max(x), num=10000)
            yHat = pwlf_.predict(xHat)

            # plot the results
            plt.figure()
            plt.plot(x, y, "o", label="Shifted")
            plt.plot(xHat, yHat, "-", label="Predicted")
            plt.plot(x_, y_, "x", label="Original")
            plt.ylabel("Recomp time / Total recomp time")
            plt.xlabel("Memory discarded / Total memory")
            plt.legend()
            plt.title(f"{filename}")
            plt.suptitle(
                f"Total Memory = {sac_memory} B Total Runtime = {sac_runtime:.4f} ms",
                fontsize=10,
            )
            folder_name = "tradeoff_graphs"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            # Save the plots in the folder
            plt.savefig(os.path.join(folder_name, f"{filename}.png"))

        if save_tradeoff_graph:
            save_prediction_graph(tradeoff_pwlf, x, y, filename)
        # 9. Obtain the slopes, intercepts and breakpoints of the fitted piecewise linear functions
        slopes = tradeoff_pwlf.calc_slopes().tolist()
        if not (
            isinstance(tradeoff_pwlf.intercepts, np.ndarray)
            and isinstance(tradeoff_pwlf.fit_breaks, np.ndarray)
        ):
            raise AssertionError
        intercepts = tradeoff_pwlf.intercepts.tolist()
        fit_breaks = tradeoff_pwlf.fit_breaks.tolist()
        return SACTradeOffStats(
            n_segments=n_segments,
            slopes=slopes,
            intercepts=intercepts,  # type: ignore[arg-type]
            fit_breaks=fit_breaks,  # type: ignore[arg-type]
            tradeoff_curve=tradeoff_curve,
            sac_memory=sac_memory,
            sac_runtime=sac_runtime,
        )