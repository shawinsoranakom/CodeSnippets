def display_sac_stats(
        self, sac_stats: SACStats, print_tabular: bool = False
    ) -> None:
        """
        Displays the SAC statistics.

        Args:
            sac_stats (SACStats): The SAC statistics to display.
            print_tabular (bool, optional): Whether to print the statistics in a tabular format. Defaults to False.

        Prints:
            1. Total Memory: The total memory usage in bytes.
            2. Total Runtime: The total runtime in milliseconds.
            3. Store Random: A flag indicating whether to force store random operator results.

            Followed by a table with the following columns:
            1. Op Idx: The operator index.
            2. Op Name: The operator name.
            3. Runtimes (ms): The operator runtime in milliseconds.
            4. Memory (B): The operator memory usage in bytes.
            5. View-like: A flag indicating whether the operator is view-like.
            6. Random: A flag indicating whether the operator is random.
            7. Saved Autograd: A flag indicating whether the operator's result is saved by autograd engine.
            8. In-place: The index of the operator's first parent, or None if not in-place.

        If print_tabular is True, the table is printed in a tabular format.
        Otherwise, the table is printed in a plain text format.
        """
        print(
            f"Total Memory: {sum(sac_stats.memory)} B Total Runtime: {sum(sac_stats.runtimes)} ms"
            f" Store Random: {sac_stats.force_store_random}"
        )
        table_data = []
        op_parent = dict(sac_stats.inplace_ops)
        for i, fn_name in enumerate(sac_stats.func_names):
            row = [
                str(i),
                fn_name,
                f"{sac_stats.runtimes[i]:.4f}",
                str(sac_stats.memory[i]),
                str(i in sac_stats.view_like_ops),
                str(i in sac_stats.rand_ops),
                str(i in sac_stats.saved_autograd_ops),
                str(op_parent.get(i)),
            ]
            table_data.append(row)
        # Define headers
        headers = [
            "Op Idx",
            "Op Name",
            "Runtimes(ms)",
            "Memory (B)",
            "View-like",
            "Random",
            "Saved Autograd",
            "In-place",
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