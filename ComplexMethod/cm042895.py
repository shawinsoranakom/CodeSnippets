async def _make_api_request(
        self,
        chunk: List[str],
        batch_idx: int,
        total_batches: int,
        semaphore: asyncio.Semaphore
        # No memory tracker
    ) -> Dict:
        """Makes a single API request for a chunk of URLs, handling concurrency and logging server memory."""
        request_success = False
        success_urls = 0
        failed_urls = 0
        status = "Pending"
        status_color = "grey"
        server_memory_metric = None # Store delta (batch) or max snapshot (stream)
        api_call_start_time = time.time()

        async with semaphore:
            try:
                # No client memory sampling

                endpoint = "/crawl/stream" if self.stream_mode else "/crawl"
                payload = {
                    "urls": chunk,
                    "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
                    "crawler_config": {
                        "type": "CrawlerRunConfig",
                        "params": {"cache_mode": "BYPASS", "stream": self.stream_mode}
                    }
                }

                if self.stream_mode:
                    max_server_mem_snapshot = 0.0 # Track max memory seen in this stream
                    async with self.http_client.stream("POST", endpoint, json=payload) as response:
                        initial_status_code = response.status_code
                        response.raise_for_status()

                        completed_marker_received = False
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    if data.get("status") == "completed":
                                        completed_marker_received = True
                                        break
                                    elif data.get("url"):
                                        if data.get("success"): success_urls += 1
                                        else: failed_urls += 1
                                        # Extract server memory snapshot per result
                                        mem_snapshot = data.get('server_memory_mb')
                                        if mem_snapshot is not None:
                                            max_server_mem_snapshot = max(max_server_mem_snapshot, float(mem_snapshot))
                                except json.JSONDecodeError:
                                    console.print(f"[Batch {batch_idx}] [red]Stream decode error for line:[/red] {line}")
                                    failed_urls = len(chunk)
                                    break
                        request_success = completed_marker_received
                        if not request_success:
                             failed_urls = len(chunk) - success_urls
                        server_memory_metric = max_server_mem_snapshot # Use max snapshot for stream logging

                else: # Batch mode
                    response = await self.http_client.post(endpoint, json=payload)
                    response.raise_for_status()
                    data = response.json()

                    # Extract server memory delta from the response
                    server_memory_metric = data.get('server_memory_delta_mb')
                    server_peak_mem_mb = data.get('server_peak_memory_mb') 

                    if data.get("success") and "results" in data:
                        request_success = True
                        results_list = data.get("results", [])
                        for result_item in results_list:
                            if result_item.get("success"): success_urls += 1
                            else: failed_urls += 1
                        if len(results_list) != len(chunk):
                             console.print(f"[Batch {batch_idx}] [yellow]Warning: Result count ({len(results_list)}) doesn't match URL count ({len(chunk)})[/yellow]")
                             failed_urls = len(chunk) - success_urls
                    else:
                        request_success = False
                        failed_urls = len(chunk)
                        # Try to get memory from error detail if available
                        detail = data.get('detail')
                        if isinstance(detail, str):
                            try: detail_json = json.loads(detail)
                            except: detail_json = {}
                        elif isinstance(detail, dict):
                            detail_json = detail
                        else: detail_json = {}
                        server_peak_mem_mb = detail_json.get('server_peak_memory_mb', None)
                        server_memory_metric = detail_json.get('server_memory_delta_mb', None)
                        console.print(f"[Batch {batch_idx}] [red]API request failed:[/red] {detail_json.get('error', 'No details')}")


            except httpx.HTTPStatusError as e:
                request_success = False
                failed_urls = len(chunk)
                console.print(f"[Batch {batch_idx}] [bold red]HTTP Error {e.response.status_code}:[/] {e.request.url}")
                try:
                    error_detail = e.response.json()
                    # Attempt to extract memory info even from error responses
                    detail_content = error_detail.get('detail', {})
                    if isinstance(detail_content, str): # Handle if detail is stringified JSON
                         try: detail_content = json.loads(detail_content)
                         except: detail_content = {}
                    server_memory_metric = detail_content.get('server_memory_delta_mb', None)
                    server_peak_mem_mb = detail_content.get('server_peak_memory_mb', None)
                    console.print(f"Response: {error_detail}")
                except Exception:
                     console.print(f"Response Text: {e.response.text[:200]}...")
            except httpx.RequestError as e:
                request_success = False
                failed_urls = len(chunk)
                console.print(f"[Batch {batch_idx}] [bold red]Request Error:[/bold] {e.request.url} - {e}")
            except Exception as e:
                request_success = False
                failed_urls = len(chunk)
                console.print(f"[Batch {batch_idx}] [bold red]Unexpected Error:[/bold] {e}")
                import traceback
                traceback.print_exc()

            finally:
                api_call_time = time.time() - api_call_start_time
                total_processed_urls = success_urls + failed_urls

                if request_success and failed_urls == 0: status_color, status = "green", "Success"
                elif request_success and success_urls > 0: status_color, status = "yellow", "Partial"
                else: status_color, status = "red", "Failed"

                current_total_urls = batch_idx * self.chunk_size
                progress_pct = min(100.0, (current_total_urls / self.url_count) * 100)
                reqs_per_sec = 1.0 / api_call_time if api_call_time > 0 else float('inf')

                # --- New Memory Formatting ---
                mem_display = " N/A " # Default
                peak_mem_value = None
                delta_or_max_value = None

                if self.stream_mode:
                    # server_memory_metric holds max snapshot for stream
                    if server_memory_metric is not None:
                        mem_display = f"{server_memory_metric:.1f} (Max)"
                        delta_or_max_value = server_memory_metric # Store for aggregation
                else: # Batch mode - expect peak and delta
                    # We need to get peak and delta from the API response
                    peak_mem_value = locals().get('server_peak_mem_mb', None) # Get from response data if available
                    delta_value = server_memory_metric # server_memory_metric holds delta for batch

                    if peak_mem_value is not None and delta_value is not None:
                        mem_display = f"{peak_mem_value:.1f} / {delta_value:+.1f}"
                        delta_or_max_value = delta_value # Store delta for aggregation
                    elif peak_mem_value is not None:
                         mem_display = f"{peak_mem_value:.1f} / N/A"
                    elif delta_value is not None:
                         mem_display = f"N/A / {delta_value:+.1f}"
                         delta_or_max_value = delta_value # Store delta for aggregation

                # --- Updated Print Statement with Adjusted Padding ---
                console.print(
                    f" {batch_idx:<5} | {progress_pct:6.1f}% | {mem_display:>24} | {reqs_per_sec:8.1f} | " # Increased width for memory column
                    f"{success_urls:^7}/{failed_urls:<6} | {api_call_time:8.2f} | [{status_color}]{status:<7}[/{status_color}] " # Added trailing space
                )

                # --- Updated Return Dictionary ---
                return_data = {
                    "batch_idx": batch_idx,
                    "request_success": request_success,
                    "success_urls": success_urls,
                    "failed_urls": failed_urls,
                    "time": api_call_time,
                    # Return both peak (if available) and delta/max
                    "server_peak_memory_mb": peak_mem_value, # Will be None for stream mode
                    "server_delta_or_max_mb": delta_or_max_value # Delta for batch, Max for stream
                }
                # Add back the specific batch mode delta if needed elsewhere, but delta_or_max covers it
                # if not self.stream_mode:
                #    return_data["server_memory_delta_mb"] = delta_value
                return return_data