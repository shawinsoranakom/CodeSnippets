async def run(self) -> Dict:
        """Run the stress test and return results."""
        memory_tracker = SimpleMemoryTracker(report_path=self.report_path, test_id=self.test_id)
        urls = [f"http://localhost:{self.server_port}/page_{i}.html" for i in range(self.url_count)]
        # Split URLs into chunks based on self.chunk_size
        url_chunks = [urls[i:i+self.chunk_size] for i in range(0, len(urls), self.chunk_size)]

        self.results_summary["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        start_time = time.time()

        config = CrawlerRunConfig(
            wait_for_images=False, verbose=False,
            stream=self.stream_mode, # Still pass stream mode, affects arun_many return type
            cache_mode=CacheMode.BYPASS
        )

        total_successful_urls = 0
        total_failed_urls = 0
        total_urls_processed = 0
        start_memory_sample = memory_tracker.sample()
        start_memory_str = start_memory_sample.get("memory_str", "Unknown")

        # monitor = CrawlerMonitor(display_mode=self.monitor_mode, total_urls=self.url_count)
        monitor = None
        rate_limiter = RateLimiter(base_delay=(0.1, 0.3)) if self.use_rate_limiter else None
        dispatcher = MemoryAdaptiveDispatcher(max_session_permit=self.max_sessions, monitor=monitor, rate_limiter=rate_limiter)

        console.print(f"\n[bold cyan]Crawl4AI Stress Test - {self.url_count} URLs, {self.max_sessions} max sessions[/bold cyan]")
        console.print(f"[bold cyan]Mode:[/bold cyan] {'Streaming' if self.stream_mode else 'Batch'}, [bold cyan]Monitor:[/bold cyan] {self.monitor_mode.name}, [bold cyan]Chunk Size:[/bold cyan] {self.chunk_size}")
        console.print(f"[bold cyan]Initial Memory:[/bold cyan] {start_memory_str}")

        # Print batch log header only if not streaming
        if not self.stream_mode:
            console.print("\n[bold]Batch Progress:[/bold] (Monitor below shows overall progress)")
            console.print("[bold] Batch | Progress | Start Mem | End Mem   | URLs/sec | Success/Fail | Time (s) | Status [/bold]")
            console.print("─" * 90)

        monitor_task = asyncio.create_task(self._periodic_memory_sample(memory_tracker, 2.0))

        try:
            async with AsyncWebCrawler(
                    config=BrowserConfig( verbose = False)
                ) as crawler:
                # Process URLs chunk by chunk
                for chunk_idx, url_chunk in enumerate(url_chunks):
                    batch_start_time = time.time()
                    chunk_success = 0
                    chunk_failed = 0

                    # Sample memory before the chunk
                    start_mem_sample = memory_tracker.sample()
                    start_mem_str = start_mem_sample.get("memory_str", "Unknown")

                    # --- Call arun_many for the current chunk ---
                    try:
                        # Note: dispatcher/monitor persist across calls
                        results_gen_or_list: Union[AsyncGenerator[CrawlResult, None], List[CrawlResult]] = \
                            await crawler.arun_many(
                                urls=url_chunk,
                                config=config,
                                dispatcher=dispatcher # Reuse the same dispatcher
                            )

                        if self.stream_mode:
                            # Process stream results if needed, but batch logging is less relevant
                            async for result in results_gen_or_list:
                                total_urls_processed += 1
                                if result.success: chunk_success += 1
                                else: chunk_failed += 1
                            # In stream mode, batch summary isn't as meaningful here
                            # We could potentially track completion per chunk async, but it's complex

                        else: # Batch mode
                            # Process the list of results for this chunk
                            for result in results_gen_or_list:
                                total_urls_processed += 1
                                if result.success: chunk_success += 1
                                else: chunk_failed += 1

                    except Exception as e:
                        console.print(f"[bold red]Error processing chunk {chunk_idx+1}: {e}[/bold red]")
                        chunk_failed = len(url_chunk) # Assume all failed in the chunk on error
                        total_urls_processed += len(url_chunk) # Count them as processed (failed)

                    # --- Log batch results (only if not streaming) ---
                    if not self.stream_mode:
                        batch_time = time.time() - batch_start_time
                        urls_per_sec = len(url_chunk) / batch_time if batch_time > 0 else 0
                        end_mem_sample = memory_tracker.sample()
                        end_mem_str = end_mem_sample.get("memory_str", "Unknown")

                        progress_pct = (total_urls_processed / self.url_count) * 100

                        if chunk_failed == 0: status_color, status = "green", "Success"
                        elif chunk_success == 0: status_color, status = "red", "Failed"
                        else: status_color, status = "yellow", "Partial"

                        console.print(
                             f" {chunk_idx+1:<5} | {progress_pct:6.1f}% | {start_mem_str:>9} | {end_mem_str:>9} | {urls_per_sec:8.1f} | "
                            f"{chunk_success:^7}/{chunk_failed:<6} | {batch_time:8.2f} | [{status_color}]{status:<7}[/{status_color}]"
                        )

                    # Accumulate totals
                    total_successful_urls += chunk_success
                    total_failed_urls += chunk_failed
                    self.results_summary["chunks_processed"] += 1

                    # Optional small delay between starting chunks if needed
                    # await asyncio.sleep(0.1)

        except Exception as e:
             console.print(f"[bold red]An error occurred during the main crawl loop: {e}[/bold red]")
        finally:
            if 'monitor_task' in locals() and not monitor_task.done():
                 monitor_task.cancel()
                 try: await monitor_task
                 except asyncio.CancelledError: pass

        end_time = time.time()
        self.results_summary.update({
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time_seconds": end_time - start_time,
            "successful_urls": total_successful_urls,
            "failed_urls": total_failed_urls,
            "urls_processed": total_urls_processed,
            "memory": memory_tracker.get_report()
        })
        self._save_results()
        return self.results_summary