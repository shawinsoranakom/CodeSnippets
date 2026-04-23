def print_stats(self, sort=-1, limit=None, show_summary=True, mode=None):
        """Print formatted statistics to stdout."""
        # Create stats object
        stats = pstats.SampledStats(self).strip_dirs()
        if not stats.stats:
            print("No samples were collected.")
            if mode == PROFILING_MODE_CPU:
                print("This can happen in CPU mode when all threads are idle.")
            return

        # Get the stats data
        stats_list = []
        for func, (
            direct_calls,
            cumulative_calls,
            total_time,
            cumulative_time,
            callers,
        ) in stats.stats.items():
            stats_list.append(
                (
                    func,
                    direct_calls,
                    cumulative_calls,
                    total_time,
                    cumulative_time,
                    callers,
                )
            )

        # Calculate total samples for percentage calculations (using direct_calls)
        total_samples = sum(
            direct_calls for _, direct_calls, _, _, _, _ in stats_list
        )

        # Sort based on the requested field
        sort_field = sort
        if sort_field == -1:  # stdname
            stats_list.sort(key=lambda x: str(x[0]))
        elif sort_field == 0:  # nsamples (direct samples)
            stats_list.sort(key=lambda x: x[1], reverse=True)  # direct_calls
        elif sort_field == 1:  # tottime
            stats_list.sort(key=lambda x: x[3], reverse=True)  # total_time
        elif sort_field == 2:  # cumtime
            stats_list.sort(key=lambda x: x[4], reverse=True)  # cumulative_time
        elif sort_field == 3:  # sample%
            stats_list.sort(
                key=lambda x: (x[1] / total_samples * 100)
                if total_samples > 0
                else 0,
                reverse=True,  # direct_calls percentage
            )
        elif sort_field == 4:  # cumul%
            stats_list.sort(
                key=lambda x: (x[2] / total_samples * 100)
                if total_samples > 0
                else 0,
                reverse=True,  # cumulative_calls percentage
            )
        elif sort_field == 5:  # nsamples (cumulative samples)
            stats_list.sort(key=lambda x: x[2], reverse=True)  # cumulative_calls

        # Apply limit if specified
        if limit is not None:
            stats_list = stats_list[:limit]

        # Determine the best unit for time columns based on maximum values
        max_total_time = max(
            (total_time for _, _, _, total_time, _, _ in stats_list), default=0
        )
        max_cumulative_time = max(
            (cumulative_time for _, _, _, _, cumulative_time, _ in stats_list),
            default=0,
        )

        total_time_unit, total_time_scale = self._determine_best_unit(max_total_time)
        cumulative_time_unit, cumulative_time_scale = self._determine_best_unit(
            max_cumulative_time
        )

        # Define column widths for consistent alignment
        col_widths = {
            "nsamples": 15,  # "nsamples" column (inline/cumulative format)
            "sample_pct": 8,  # "sample%" column
            "tottime": max(12, len(f"tottime ({total_time_unit})")),
            "cum_pct": 8,  # "cumul%" column
            "cumtime": max(12, len(f"cumtime ({cumulative_time_unit})")),
        }

        # Print header with colors and proper alignment
        print(f"{ANSIColors.BOLD_BLUE}Profile Stats:{ANSIColors.RESET}")

        header_nsamples = f"{ANSIColors.BOLD_BLUE}{'nsamples':>{col_widths['nsamples']}}{ANSIColors.RESET}"
        header_sample_pct = f"{ANSIColors.BOLD_BLUE}{'sample%':>{col_widths['sample_pct']}}{ANSIColors.RESET}"
        header_tottime = f"{ANSIColors.BOLD_BLUE}{f'tottime ({total_time_unit})':>{col_widths['tottime']}}{ANSIColors.RESET}"
        header_cum_pct = f"{ANSIColors.BOLD_BLUE}{'cumul%':>{col_widths['cum_pct']}}{ANSIColors.RESET}"
        header_cumtime = f"{ANSIColors.BOLD_BLUE}{f'cumtime ({cumulative_time_unit})':>{col_widths['cumtime']}}{ANSIColors.RESET}"
        header_filename = (
            f"{ANSIColors.BOLD_BLUE}filename:lineno(function){ANSIColors.RESET}"
        )

        print(
            f"{header_nsamples}  {header_sample_pct}  {header_tottime}  {header_cum_pct}  {header_cumtime}  {header_filename}"
        )

        # Print each line with proper alignment
        for (
            func,
            direct_calls,
            cumulative_calls,
            total_time,
            cumulative_time,
            callers,
        ) in stats_list:
            # Calculate percentages
            sample_pct = (
                (direct_calls / total_samples * 100) if total_samples > 0 else 0
            )
            cum_pct = (
                (cumulative_calls / total_samples * 100)
                if total_samples > 0
                else 0
            )

            # Format values with proper alignment - always use A/B format
            nsamples_str = f"{direct_calls}/{cumulative_calls}"
            nsamples_str = f"{nsamples_str:>{col_widths['nsamples']}}"
            sample_pct_str = f"{sample_pct:{col_widths['sample_pct']}.1f}"
            tottime = f"{total_time * total_time_scale:{col_widths['tottime']}.3f}"
            cum_pct_str = f"{cum_pct:{col_widths['cum_pct']}.1f}"
            cumtime = f"{cumulative_time * cumulative_time_scale:{col_widths['cumtime']}.3f}"

            # Format the function name with colors
            func_name = (
                f"{ANSIColors.GREEN}{func[0]}{ANSIColors.RESET}:"
                f"{ANSIColors.YELLOW}{func[1]}{ANSIColors.RESET}("
                f"{ANSIColors.CYAN}{func[2]}{ANSIColors.RESET})"
            )

            # Print the formatted line with consistent spacing
            print(
                f"{nsamples_str}  {sample_pct_str}  {tottime}  {cum_pct_str}  {cumtime}  {func_name}"
            )

        # Print legend
        print(f"\n{ANSIColors.BOLD_BLUE}Legend:{ANSIColors.RESET}")
        print(
            f"  {ANSIColors.YELLOW}nsamples{ANSIColors.RESET}: Direct/Cumulative samples (direct executing / on call stack)"
        )
        print(
            f"  {ANSIColors.YELLOW}sample%{ANSIColors.RESET}: Percentage of total samples this function was directly executing"
        )
        print(
            f"  {ANSIColors.YELLOW}tottime{ANSIColors.RESET}: Estimated total time spent directly in this function"
        )
        print(
            f"  {ANSIColors.YELLOW}cumul%{ANSIColors.RESET}: Percentage of total samples when this function was on the call stack"
        )
        print(
            f"  {ANSIColors.YELLOW}cumtime{ANSIColors.RESET}: Estimated cumulative time (including time in called functions)"
        )
        print(
            f"  {ANSIColors.YELLOW}filename:lineno(function){ANSIColors.RESET}: Function location and name"
        )

        # Print summary of interesting functions if enabled
        if show_summary and stats_list:
            self._print_summary(stats_list, total_samples)