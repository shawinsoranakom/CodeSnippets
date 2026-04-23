def generate_memory_charts(self, results, output_prefix=None):
        """Generate memory usage charts for each test.

        Args:
            results: Dictionary mapping test IDs to result data
            output_prefix: Prefix for output file names

        Returns:
            List of paths to the saved chart files
        """
        if not VISUALIZATION_AVAILABLE:
            console.print("[yellow]Skipping memory charts - visualization dependencies not available[/yellow]")
            return []

        output_files = []

        for test_id, result in results.items():
            if 'memory_samples' not in result:
                continue

            memory_df = result['memory_samples']

            # Check if we have enough data points
            if len(memory_df) < 2:
                continue

            # Try to extract numeric values from memory_info strings
            try:
                memory_values = []
                for mem_str in memory_df['memory_info']:
                    # Extract the number from strings like "142.8 MB"
                    value = float(mem_str.split()[0])
                    memory_values.append(value)

                memory_df['memory_mb'] = memory_values
            except Exception as e:
                console.print(f"[yellow]Could not parse memory values for {test_id}: {e}[/yellow]")
                continue

            # Create the plot
            plt.figure(figsize=(10, 6))

            # Plot memory usage over time
            plt.plot(memory_df['elapsed_seconds'], memory_df['memory_mb'], 
                     color='#88c0d0', marker='o', linewidth=2, markersize=4)

            # Add annotations for chunk processing
            chunk_size = result.get('chunk_size', 0)
            url_count = result.get('url_count', 0)
            if chunk_size > 0 and url_count > 0:
                # Estimate chunk processing times
                num_chunks = (url_count + chunk_size - 1) // chunk_size  # Ceiling division
                total_time = result.get('total_time_seconds', memory_df['elapsed_seconds'].max())
                chunk_times = np.linspace(0, total_time, num_chunks + 1)[1:]

                for i, time_point in enumerate(chunk_times):
                    if time_point <= memory_df['elapsed_seconds'].max():
                        plt.axvline(x=time_point, color='#4c566a', linestyle='--', alpha=0.6)
                        plt.text(time_point, memory_df['memory_mb'].min(), f'Chunk {i+1}', 
                                rotation=90, verticalalignment='bottom', fontsize=8, color='#e0e0e0')

            # Set labels and title
            plt.xlabel('Elapsed Time (seconds)', color='#e0e0e0')
            plt.ylabel('Memory Usage (MB)', color='#e0e0e0')
            plt.title(f'Memory Usage During Test {test_id}\n({url_count} URLs, {result.get("workers", "?")} Workers)', 
                      color='#e0e0e0')

            # Add grid and set y-axis to start from zero
            plt.grid(True, alpha=0.3, color='#4c566a')

            # Add test metadata as text
            info_text = (
                f"URLs: {url_count}\n"
                f"Workers: {result.get('workers', 'N/A')}\n"
                f"Chunk Size: {result.get('chunk_size', 'N/A')}\n"
                f"Total Time: {result.get('total_time_seconds', 0):.2f}s\n"
            )

            # Calculate memory growth
            if len(memory_df) >= 2:
                first_mem = memory_df.iloc[0]['memory_mb']
                last_mem = memory_df.iloc[-1]['memory_mb']
                growth = last_mem - first_mem
                growth_rate = growth / result.get('total_time_seconds', 1)

                info_text += f"Memory Growth: {growth:.1f} MB\n"
                info_text += f"Growth Rate: {growth_rate:.2f} MB/s"

            plt.figtext(0.02, 0.02, info_text, fontsize=9, color='#e0e0e0',
                       bbox=dict(facecolor='#3b4252', alpha=0.8, edgecolor='#4c566a'))

            # Save the figure
            if output_prefix is None:
                output_file = self.output_dir / f"memory_chart_{test_id}.png"
            else:
                output_file = Path(f"{output_prefix}_memory_{test_id}.png")

            plt.tight_layout()
            plt.savefig(output_file, dpi=100, bbox_inches='tight')
            plt.close()

            output_files.append(output_file)

        return output_files