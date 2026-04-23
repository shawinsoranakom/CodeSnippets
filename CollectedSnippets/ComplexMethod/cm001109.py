def _generate_top_blocks_alert(
        self,
        block_stats: dict[str, BlockStatsWithSamples],
        start_time: datetime,
        end_time: datetime,
    ) -> str | None:
        """Generate top blocks summary when no critical alerts exist."""
        top_error_blocks = sorted(
            [
                (name, stats)
                for name, stats in block_stats.items()
                if stats.total_executions >= 10 and stats.failed_executions > 0
            ],
            key=lambda x: x[1].failed_executions,
            reverse=True,
        )[: self.include_top_blocks]

        if not top_error_blocks:
            return "✅ No errors reported for today - all blocks are running smoothly!"

        # Get error samples for top blocks
        for block_name, stats in top_error_blocks:
            if not stats.error_samples:
                stats.error_samples = self._get_error_samples_for_block(
                    stats.block_id, start_time, end_time, limit=2
                )

        count_text = (
            f"top {self.include_top_blocks}" if self.include_top_blocks > 1 else "top"
        )
        alert_msg = f"📊 Daily Error Summary - {count_text} blocks with most errors:"
        for block_name, stats in top_error_blocks:
            alert_msg += f"\n• {block_name}: {stats.failed_executions} errors ({stats.error_rate:.1f}% of {stats.total_executions})"

            if stats.error_samples:
                error_groups = self._group_similar_errors(stats.error_samples)
                if error_groups:
                    # Show most common error
                    most_common_error = next(iter(error_groups.items()))
                    alert_msg += f"\n  └ Most common: {most_common_error[0]}"

        return alert_msg