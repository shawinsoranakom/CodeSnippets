def _print_summary(self, stats_list, total_samples):
        """Print summary of interesting functions."""
        print(
            f"\n{ANSIColors.BOLD_BLUE}Summary of Interesting Functions:{ANSIColors.RESET}"
        )

        # Aggregate stats by fully qualified function name (ignoring line numbers)
        func_aggregated = {}
        for (
            func,
            direct_calls,
            cumulative_calls,
            total_time,
            cumulative_time,
            callers,
        ) in stats_list:
            # Use filename:function_name as the key to get fully qualified name
            qualified_name = f"{func[0]}:{func[2]}"
            if qualified_name not in func_aggregated:
                func_aggregated[qualified_name] = [
                    0,
                    0,
                    0,
                    0,
                ]  # direct_calls, cumulative_calls, total_time, cumulative_time
            func_aggregated[qualified_name][0] += direct_calls
            func_aggregated[qualified_name][1] += cumulative_calls
            func_aggregated[qualified_name][2] += total_time
            func_aggregated[qualified_name][3] += cumulative_time

        # Convert aggregated data back to list format for processing
        aggregated_stats = []
        for qualified_name, (
            prim_calls,
            total_calls,
            total_time,
            cumulative_time,
        ) in func_aggregated.items():
            # Parse the qualified name back to filename and function name
            if ":" in qualified_name:
                filename, func_name = qualified_name.rsplit(":", 1)
            else:
                filename, func_name = "", qualified_name
            # Create a dummy func tuple with filename and function name for display
            dummy_func = (filename, "", func_name)
            aggregated_stats.append(
                (
                    dummy_func,
                    prim_calls,
                    total_calls,
                    total_time,
                    cumulative_time,
                    {},
                )
            )

        # Determine best units for summary metrics
        max_total_time = max(
            (total_time for _, _, _, total_time, _, _ in aggregated_stats),
            default=0,
        )
        max_cumulative_time = max(
            (
                cumulative_time
                for _, _, _, _, cumulative_time, _ in aggregated_stats
            ),
            default=0,
        )

        total_unit, total_scale = self._determine_best_unit(max_total_time)
        cumulative_unit, cumulative_scale = self._determine_best_unit(
            max_cumulative_time
        )

        def _format_func_name(func):
            """Format function name with colors."""
            return (
                f"{ANSIColors.GREEN}{func[0]}{ANSIColors.RESET}:"
                f"{ANSIColors.YELLOW}{func[1]}{ANSIColors.RESET}("
                f"{ANSIColors.CYAN}{func[2]}{ANSIColors.RESET})"
            )

        def _print_top_functions(stats_list, title, key_func, format_line, n=3):
            """Print top N functions sorted by key_func with formatted output."""
            print(f"\n{ANSIColors.BOLD_BLUE}{title}:{ANSIColors.RESET}")
            sorted_stats = sorted(stats_list, key=key_func, reverse=True)
            for stat in sorted_stats[:n]:
                if line := format_line(stat):
                    print(f"  {line}")

        # Functions with highest direct/cumulative ratio (hot spots)
        def format_hotspots(stat):
            func, direct_calls, cumulative_calls, total_time, _, _ = stat
            if direct_calls > 0 and cumulative_calls > 0:
                ratio = direct_calls / cumulative_calls
                direct_pct = (
                    (direct_calls / total_samples * 100)
                    if total_samples > 0
                    else 0
                )
                return (
                    f"{ratio:.3f} direct/cumulative ratio, "
                    f"{direct_pct:.1f}% direct samples: {_format_func_name(func)}"
                )
            return None

        _print_top_functions(
            aggregated_stats,
            "Functions with Highest Direct/Cumulative Ratio (Hot Spots)",
            key_func=lambda x: (x[1] / x[2]) if x[2] > 0 else 0,
            format_line=format_hotspots,
        )

        # Functions with highest call frequency (cumulative/direct difference)
        def format_call_frequency(stat):
            func, direct_calls, cumulative_calls, total_time, _, _ = stat
            if cumulative_calls > direct_calls:
                call_frequency = cumulative_calls - direct_calls
                cum_pct = (
                    (cumulative_calls / total_samples * 100)
                    if total_samples > 0
                    else 0
                )
                return (
                    f"{call_frequency:d} indirect calls, "
                    f"{cum_pct:.1f}% total stack presence: {_format_func_name(func)}"
                )
            return None

        _print_top_functions(
            aggregated_stats,
            "Functions with Highest Call Frequency (Indirect Calls)",
            key_func=lambda x: x[2] - x[1],  # Sort by (cumulative - direct)
            format_line=format_call_frequency,
        )

        # Functions with highest cumulative-to-direct multiplier (call magnification)
        def format_call_magnification(stat):
            func, direct_calls, cumulative_calls, total_time, _, _ = stat
            if direct_calls > 0 and cumulative_calls > direct_calls:
                multiplier = cumulative_calls / direct_calls
                indirect_calls = cumulative_calls - direct_calls
                return (
                    f"{multiplier:.1f}x call magnification, "
                    f"{indirect_calls:d} indirect calls from {direct_calls:d} direct: {_format_func_name(func)}"
                )
            return None

        _print_top_functions(
            aggregated_stats,
            "Functions with Highest Call Magnification (Cumulative/Direct)",
            key_func=lambda x: (x[2] / x[1])
            if x[1] > 0
            else 0,  # Sort by cumulative/direct ratio
            format_line=format_call_magnification,
        )