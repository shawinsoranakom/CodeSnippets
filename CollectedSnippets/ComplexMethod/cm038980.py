def print_table(
        self,
        results: list[BenchmarkResult],
        backends: list[str],
        compare_to_fastest: bool = True,
    ):
        """
        Print results as a rich table.

        Args:
            results: List of BenchmarkResult
            backends: List of backend names being compared
            compare_to_fastest: Show percentage comparison to fastest
        """
        # Group by batch spec, preserving first-occurrence order
        by_spec = {}
        specs_order = []
        for r in results:
            spec = r.config.batch_spec
            if spec not in by_spec:
                by_spec[spec] = {}
                specs_order.append(spec)
            by_spec[spec][r.config.backend] = r

        # Sort specs by (batch_size, q_len, kv_len) instead of alphabetically
        specs_order = sorted(by_spec.keys(), key=batch_spec_sort_key)

        # Create shortened backend names for display
        def shorten_backend_name(name: str) -> str:
            """Shorten long backend names for table display."""
            # Remove common prefixes
            name = name.replace("flashattn_mla", "famla")
            name = name.replace("flashinfer_mla", "fimla")
            name = name.replace("flashmla", "fmla")
            name = name.replace("cutlass_mla", "cmla")
            name = name.replace("numsplits", "ns")
            return name

        table = Table(title="Attention Benchmark Results")
        table.add_column("Batch\nSpec", no_wrap=True)
        table.add_column("Type", no_wrap=True)
        table.add_column("Batch\nSize", justify="right", no_wrap=True)

        multi = len(backends) > 1
        for backend in backends:
            short_name = shorten_backend_name(backend)
            # Time column
            col_time = f"{short_name}\nTime (s)"
            table.add_column(col_time, justify="right", no_wrap=False)
            if multi and compare_to_fastest:
                # Relative performance column
                col_rel = f"{short_name}\nvs Best"
                table.add_column(col_rel, justify="right", no_wrap=False)

        # Add rows
        for spec in specs_order:
            spec_results = by_spec[spec]
            times = {b: r.mean_time for b, r in spec_results.items() if r.success}
            best_time = min(times.values()) if times else 0.0

            batch_type = get_batch_type(spec)
            batch_size = len(parse_batch_spec(spec))
            row = [spec, batch_type, str(batch_size)]
            for backend in backends:
                if backend in spec_results:
                    r = spec_results[backend]
                    if r.success:
                        row.append(f"{r.mean_time:.6f}")
                        if multi and compare_to_fastest:
                            pct = (
                                (r.mean_time / best_time * 100) if best_time > 0 else 0
                            )
                            pct_str = f"{pct:.1f}%"
                            if r.mean_time == best_time:
                                pct_str = f"[bold green]{pct_str}[/]"
                            row.append(pct_str)
                    else:
                        row.append("[red]ERROR[/]")
                        if multi and compare_to_fastest:
                            row.append("-")
                else:
                    row.append("-")
                    if multi and compare_to_fastest:
                        row.append("-")

            table.add_row(*row)

        self.console.print(table)