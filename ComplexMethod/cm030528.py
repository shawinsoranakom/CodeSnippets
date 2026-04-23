def build_stats_list(self):
        """Build and sort the statistics list."""
        stats_list = []
        result_source = self._get_current_result_source()

        for func, call_counts in result_source.items():
            # Apply filter if set (using substring matching)
            if self.filter_pattern:
                filename, lineno, funcname = func
                # Simple substring match (case-insensitive)
                pattern_lower = self.filter_pattern.lower()
                filename_lower = filename.lower()
                funcname_lower = funcname.lower()

                # Match if pattern is substring of filename, funcname, or combined
                matched = (
                    pattern_lower in filename_lower
                    or pattern_lower in funcname_lower
                    or pattern_lower in f"{filename_lower}:{funcname_lower}"
                )
                if not matched:
                    continue

            direct_calls = call_counts.get("direct_calls", 0)
            cumulative_calls = call_counts.get("cumulative_calls", 0)
            total_time = direct_calls * self.sample_interval_sec
            cumulative_time = cumulative_calls * self.sample_interval_sec

            # Calculate sample percentages using successful_samples as denominator
            # This ensures percentages are relative to samples that actually had data,
            # not all sampling attempts (important for filtered modes like --mode exception)
            sample_pct = (direct_calls / self.successful_samples * 100) if self.successful_samples > 0 else 0
            cumul_pct = (cumulative_calls / self.successful_samples * 100) if self.successful_samples > 0 else 0

            # Calculate trends for all columns using TrendTracker
            trends = {}
            if self._trend_tracker is not None:
                trends = self._trend_tracker.update_metrics(
                    func,
                    {
                        'nsamples': direct_calls,
                        'tottime': total_time,
                        'cumtime': cumulative_time,
                        'sample_pct': sample_pct,
                        'cumul_pct': cumul_pct,
                    }
                )

            stats_list.append(
                {
                    "func": func,
                    "direct_calls": direct_calls,
                    "cumulative_calls": cumulative_calls,
                    "total_time": total_time,
                    "cumulative_time": cumulative_time,
                    "sample_pct": sample_pct,
                    "cumul_pct": cumul_pct,
                    "trends": trends,
                }
            )

        # Sort the stats
        if self.sort_by == "nsamples":
            stats_list.sort(key=lambda x: x["direct_calls"], reverse=True)
        elif self.sort_by == "tottime":
            stats_list.sort(key=lambda x: x["total_time"], reverse=True)
        elif self.sort_by == "cumtime":
            stats_list.sort(key=lambda x: x["cumulative_time"], reverse=True)
        elif self.sort_by == "sample_pct":
            stats_list.sort(key=lambda x: x["sample_pct"], reverse=True)
        elif self.sort_by == "cumul_pct":
            stats_list.sort(key=lambda x: x["cumul_pct"], reverse=True)

        return stats_list