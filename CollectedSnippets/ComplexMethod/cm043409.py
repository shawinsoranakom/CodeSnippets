def _create_task_details_panel(self) -> Panel:
        """Create the task details panel."""
        # Create a table for task details
        table = Table(show_header=True, expand=True)
        table.add_column("Task ID", style="cyan", no_wrap=True, width=10)
        table.add_column("URL", style="blue", ratio=3)
        table.add_column("Status", style="green", width=15)
        table.add_column("Memory", justify="right", width=8)
        table.add_column("Peak", justify="right", width=8)
        table.add_column("Duration", justify="right", width=10)

        # Get all task stats
        task_stats = self.monitor.get_all_task_stats()

        # Add summary row
        active_tasks = sum(1 for stats in task_stats.values() 
                          if stats['status'] == CrawlStatus.IN_PROGRESS.name)

        total_memory = sum(stats['memory_usage'] for stats in task_stats.values())
        total_peak = sum(stats['peak_memory'] for stats in task_stats.values())

        # Summary row with separators
        table.add_row(
            "SUMMARY", 
            f"Total: {len(task_stats)}", 
            f"Active: {active_tasks}",
            f"{total_memory:.1f}",
            f"{total_peak:.1f}",
            "N/A"
        )

        # Add a separator
        table.add_row("—" * 10, "—" * 20, "—" * 10, "—" * 8, "—" * 8, "—" * 10)

        # Status icons
        status_icons = {
            CrawlStatus.QUEUED.name: "⏳",
            CrawlStatus.IN_PROGRESS.name: "🔄",
            CrawlStatus.COMPLETED.name: "✅",
            CrawlStatus.FAILED.name: "❌"
        }

        # Calculate how many rows we can display based on available space
        # We can display more rows now that we have a dedicated panel
        display_count = min(len(task_stats), 20)  # Display up to 20 tasks

        # Add rows for each task
        for task_id, stats in sorted(
            list(task_stats.items())[:display_count],
            # Sort: 1. IN_PROGRESS first, 2. QUEUED, 3. COMPLETED/FAILED by recency
            key=lambda x: (
                0 if x[1]['status'] == CrawlStatus.IN_PROGRESS.name else 
                1 if x[1]['status'] == CrawlStatus.QUEUED.name else 
                2,
                -1 * (x[1].get('end_time', 0) or 0)  # Most recent first
            )
        ):
            # Truncate task_id and URL for display
            short_id = task_id[:8]
            url = stats['url']
            if len(url) > 50:  # Allow longer URLs in the dedicated panel
                url = url[:47] + "..."

            # Format status with icon
            status = f"{status_icons.get(stats['status'], '?')} {stats['status']}"

            # Add row
            table.add_row(
                short_id,
                url,
                status,
                f"{stats['memory_usage']:.1f}",
                f"{stats['peak_memory']:.1f}",
                stats['duration'] if 'duration' in stats else "0:00"
            )

        return Panel(table, title="Task Details", border_style="yellow")