def display_sac_tradeoff_stats(
        self,
        greedy_order_meta: SACGreedyOrderMeta,
        sac_stats: SACStats,
        print_tabular: bool = False,
    ) -> None:
        """
        Displays the SAC trade-off statistics.

        Args:
            greedy_order_meta (SACGreedyOrderMeta): The SAC greedy order metadata.
            sac_stats (SACStats): The SAC statistics.
            print_tabular (bool, optional): Whether to print the statistics in a tabular format. Defaults to False.

        Prints:
            A table with the following columns:
            1. Op Id(s): The operator index(es).
            2. Op Name(s): The operator name(s).
            3. Discarded Mem (%): The percentage of discarded memory.
            4. Discarded Mem (B): The discarded memory in bytes.
            5. Recomp time (%): The percentage of recomputed time.
            6. Recomp time (ms): The recomputed time in milliseconds.
            7. MSPS: The memory per second.
            8. Always Stored: A flag indicating whether the operator is always stored.
            9. Always Recomputed: A flag indicating whether the operator is always recomputed.

        If print_tabular is True, the table is printed in a tabular format.
        Otherwise, the table is printed in a plain text format.
        """
        table_data = []
        total_memory, total_runtime = sum(sac_stats.memory), sum(sac_stats.runtimes)
        discarded_mem: int = 0
        recomp_runtime: float = 0.0

        def append_row(
            op_indices: set[int],
            func_names: set[str],
            msps: float | None = None,
            stored: bool | None = False,
            recomputed: bool | None = False,
        ) -> None:
            row = [
                str(op_indices),
                str(func_names),
                f"{discarded_mem / total_memory:.4f}",
                str(discarded_mem),
                f"{recomp_runtime / total_runtime:.4f}",
                str(recomp_runtime),
                f"{msps:.2e}" if msps is not None else str(nan),
                str(stored),
                str(recomputed),
            ]
            table_data.append(row)

        stored_ops, recomputed_ops, inplace_op_groups, random_ops_group, msps_meta = (
            greedy_order_meta.stored_ops,
            greedy_order_meta.recomputed_ops,
            greedy_order_meta.inplace_op_groups,
            greedy_order_meta.random_ops_group,
            greedy_order_meta.msps_meta,
        )

        for op_idx in recomputed_ops:
            op_indices: set[int] = {op_idx}
            if op_idx in inplace_op_groups:
                op_indices.update(inplace_op_groups[op_idx])
            if op_idx in random_ops_group:
                op_indices.update(random_ops_group[op_idx])
            discarded_mem += sum(sac_stats.memory[i] for i in op_indices)
            recomp_runtime += sum(sac_stats.runtimes[i] for i in op_indices)
            func_names = {sac_stats.func_names[i] for i in op_indices}
            append_row(op_indices, func_names, recomputed=True)

        for cand in msps_meta:
            discarded_mem += cand.memory
            recomp_runtime += cand.runtime
            op_indices = {cand.op_idx}
            if cand.op_idx in inplace_op_groups:
                op_indices.update(inplace_op_groups[cand.op_idx])
            if cand.op_idx in random_ops_group:
                op_indices.update(random_ops_group[cand.op_idx])
            append_row(op_indices, cand.func_names, msps=cand.msps)

        for op_idx in stored_ops:
            op_indices = {op_idx}
            if op_idx in inplace_op_groups:
                op_indices.update(inplace_op_groups[op_idx])
            if op_idx in random_ops_group:
                op_indices.update(random_ops_group[op_idx])
            discarded_mem += sum(sac_stats.memory[i] for i in op_indices)
            recomp_runtime += sum(sac_stats.runtimes[i] for i in op_indices)
            func_names = {sac_stats.func_names[i] for i in op_indices}
            append_row(op_indices, func_names, stored=True)

        headers = [
            "Op Id(s)",
            "Op Name(s)",
            "Discarded Mem (%)",
            "Discarded Mem (B)",
            "Recomp time (%)",
            "Recomp time (ms)",
            "MSPS",
            "Always Stored",
            "Always Recomputed",
        ]
        if print_tabular:
            _display_stats_tabular(headers, table_data)
        else:
            max_widths = [0 for _ in range(len(headers))]
            table_data.insert(0, headers)
            for row in table_data:
                for i, elem in enumerate(row):
                    max_widths[i] = max(max_widths[i], len(elem))
            for row in table_data:
                print(
                    "\t".join(
                        [f"{elem:<{max_widths[i]}}" for i, elem in enumerate(row)]
                    )
                )