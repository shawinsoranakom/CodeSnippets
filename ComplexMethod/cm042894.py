async def run(self) -> Dict:
        """Run the API stress test."""
        # No client memory tracker needed
        urls_to_process = [f"https://httpbin.org/anything/{uuid.uuid4()}" for _ in range(self.url_count)]
        url_chunks = [urls_to_process[i:i+self.chunk_size] for i in range(0, len(urls_to_process), self.chunk_size)]

        self.results_summary["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        start_time = time.time()

        console.print(f"\n[bold cyan]Crawl4AI API Stress Test - {self.url_count} URLs, {self.max_concurrent_requests} concurrent requests[/bold cyan]")
        console.print(f"[bold cyan]Target API:[/bold cyan] {self.api_base_url}, [bold cyan]Mode:[/bold cyan] {'Streaming' if self.stream_mode else 'Batch'}, [bold cyan]URLs per Request:[/bold cyan] {self.chunk_size}")
        # Removed client memory log

        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        # Updated Batch logging header
        console.print("\n[bold]API Request Batch Progress:[/bold]")
        # Adjusted spacing and added Peak
        console.print("[bold] Batch | Progress | SrvMem Peak / Δ|Max (MB) | Reqs/sec | S/F URLs | Time (s) | Status  [/bold]")
        # Adjust separator length if needed, looks okay for now
        console.print("─" * 95) 

        # No client memory monitor task needed

        tasks = []
        total_api_calls = len(url_chunks)
        self.results_summary["total_api_calls"] = total_api_calls

        try:
            for i, chunk in enumerate(url_chunks):
                task = asyncio.create_task(self._make_api_request(
                    chunk=chunk,
                    batch_idx=i + 1,
                    total_batches=total_api_calls,
                    semaphore=semaphore
                    # No memory tracker passed
                ))
                tasks.append(task)

            api_results = await asyncio.gather(*tasks)

            # Process aggregated results including server memory
            total_successful_requests = sum(1 for r in api_results if r['request_success'])
            total_failed_requests = total_api_calls - total_successful_requests
            total_successful_urls = sum(r['success_urls'] for r in api_results)
            total_failed_urls = sum(r['failed_urls'] for r in api_results)
            total_urls_processed = total_successful_urls + total_failed_urls

            # Aggregate server memory metrics
            valid_samples = [r for r in api_results if r.get('server_delta_or_max_mb') is not None] # Filter results with valid mem data
            self.results_summary["server_memory_metrics"]["samples"] = valid_samples # Store raw samples with both peak and delta/max

            if valid_samples:
                 delta_or_max_values = [r['server_delta_or_max_mb'] for r in valid_samples]
                 if self.stream_mode:
                     # Stream mode: delta_or_max holds max snapshot
                     self.results_summary["server_memory_metrics"]["stream_mode_avg_max_snapshot_mb"] = sum(delta_or_max_values) / len(delta_or_max_values)
                     self.results_summary["server_memory_metrics"]["stream_mode_max_max_snapshot_mb"] = max(delta_or_max_values)
                 else: # Batch mode
                     # delta_or_max holds delta
                     self.results_summary["server_memory_metrics"]["batch_mode_avg_delta_mb"] = sum(delta_or_max_values) / len(delta_or_max_values)
                     self.results_summary["server_memory_metrics"]["batch_mode_max_delta_mb"] = max(delta_or_max_values)

                     # Aggregate peak values for batch mode
                     peak_values = [r['server_peak_memory_mb'] for r in valid_samples if r.get('server_peak_memory_mb') is not None]
                     if peak_values:
                          self.results_summary["server_memory_metrics"]["batch_mode_avg_peak_mb"] = sum(peak_values) / len(peak_values)
                          self.results_summary["server_memory_metrics"]["batch_mode_max_peak_mb"] = max(peak_values)


            self.results_summary.update({
                "successful_requests": total_successful_requests,
                "failed_requests": total_failed_requests,
                "successful_urls": total_successful_urls,
                "failed_urls": total_failed_urls,
                "total_urls_processed": total_urls_processed,
            })

        except Exception as e:
             console.print(f"[bold red]An error occurred during task execution: {e}[/bold red]")
             import traceback
             traceback.print_exc()
        # No finally block needed for monitor task

        end_time = time.time()
        self.results_summary.update({
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time_seconds": end_time - start_time,
            # No client memory report
        })
        self._save_results()
        return self.results_summary