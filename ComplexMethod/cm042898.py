def generate_summary_table(self, results):
        """Generate a summary table of test results.

        Args:
            results: Dictionary mapping test IDs to result data

        Returns:
            Rich Table object
        """
        table = Table(title="Crawl4AI Stress Test Summary", show_header=True)

        # Define columns
        table.add_column("Test ID", style="cyan")
        table.add_column("Date", style="bright_green")
        table.add_column("URLs", justify="right")
        table.add_column("Workers", justify="right")
        table.add_column("Success %", justify="right")
        table.add_column("Time (s)", justify="right")
        table.add_column("Mem Growth", justify="right")
        table.add_column("URLs/sec", justify="right")

        # Add rows
        for test_id, data in sorted(results.items(), key=lambda x: x[0], reverse=True):
            # Parse timestamp from test_id
            try:
                date_str = datetime.strptime(test_id, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M")
            except:
                date_str = "Unknown"

            # Calculate success percentage
            total_urls = data.get('url_count', 0)
            successful = data.get('successful_urls', 0)
            success_pct = (successful / total_urls * 100) if total_urls > 0 else 0

            # Calculate memory growth if available
            mem_growth = "N/A"
            if 'memory_samples' in data:
                samples = data['memory_samples']
                if len(samples) >= 2:
                    # Try to extract numeric values from memory_info strings
                    try:
                        first_mem = float(samples.iloc[0]['memory_info'].split()[0])
                        last_mem = float(samples.iloc[-1]['memory_info'].split()[0])
                        mem_growth = f"{last_mem - first_mem:.1f} MB"
                    except:
                        pass

            # Calculate URLs per second
            time_taken = data.get('total_time_seconds', 0)
            urls_per_sec = total_urls / time_taken if time_taken > 0 else 0

            table.add_row(
                test_id,
                date_str,
                str(total_urls),
                str(data.get('workers', 'N/A')),
                f"{success_pct:.1f}%",
                f"{data.get('total_time_seconds', 0):.2f}",
                mem_growth,
                f"{urls_per_sec:.1f}"
            )

        return table