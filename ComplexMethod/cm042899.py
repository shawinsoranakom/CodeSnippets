def generate_performance_chart(self, results, output_file=None):
        """Generate a performance comparison chart.

        Args:
            results: Dictionary mapping test IDs to result data
            output_file: File path to save the chart

        Returns:
            Path to the saved chart file or None if visualization is not available
        """
        if not VISUALIZATION_AVAILABLE:
            console.print("[yellow]Skipping performance chart - visualization dependencies not available[/yellow]")
            return None

        # Extract relevant data
        data = []
        for test_id, result in results.items():
            urls = result.get('url_count', 0)
            workers = result.get('workers', 0)
            time_taken = result.get('total_time_seconds', 0)
            urls_per_sec = urls / time_taken if time_taken > 0 else 0

            # Parse timestamp from test_id for sorting
            try:
                timestamp = datetime.strptime(test_id, "%Y%m%d_%H%M%S")
                data.append({
                    'test_id': test_id,
                    'timestamp': timestamp,
                    'urls': urls,
                    'workers': workers,
                    'time_seconds': time_taken,
                    'urls_per_sec': urls_per_sec
                })
            except:
                console.print(f"[yellow]Warning: Could not parse timestamp from {test_id}[/yellow]")

        if not data:
            console.print("[yellow]No valid data for performance chart[/yellow]")
            return None

        # Convert to DataFrame and sort by timestamp
        df = pd.DataFrame(data)
        df = df.sort_values('timestamp')

        # Create the plot
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Plot URLs per second as bars with properly set x-axis
        x_pos = range(len(df['test_id']))
        bars = ax1.bar(x_pos, df['urls_per_sec'], color='#88c0d0', alpha=0.8)
        ax1.set_ylabel('URLs per Second', color='#88c0d0')
        ax1.tick_params(axis='y', labelcolor='#88c0d0')

        # Properly set x-axis labels
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(df['test_id'].tolist(), rotation=45, ha='right')

        # Add worker count as text on each bar
        for i, bar in enumerate(bars):
            height = bar.get_height()
            workers = df.iloc[i]['workers']
            ax1.text(i, height + 0.1,
                    f'W: {workers}', ha='center', va='bottom', fontsize=9, color='#e0e0e0')

        # Add a second y-axis for total URLs
        ax2 = ax1.twinx()
        ax2.plot(x_pos, df['urls'], '-', color='#bf616a', alpha=0.8, markersize=6, marker='o')
        ax2.set_ylabel('Total URLs', color='#bf616a')
        ax2.tick_params(axis='y', labelcolor='#bf616a')

        # Set title and layout
        plt.title('Crawl4AI Performance Benchmarks')
        plt.tight_layout()

        # Save the figure
        if output_file is None:
            output_file = self.output_dir / "performance_comparison.png"
        plt.savefig(output_file, dpi=100, bbox_inches='tight')
        plt.close()

        return output_file