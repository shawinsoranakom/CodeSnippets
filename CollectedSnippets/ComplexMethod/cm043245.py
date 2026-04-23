async def crawl_url(
        self,
        url: str,
        config: Union[CrawlerRunConfig, List[CrawlerRunConfig]],
        task_id: str,
        retry_count: int = 0,
    ) -> CrawlerTaskResult:
        start_time = time.time()
        error_message = ""
        memory_usage = peak_memory = 0.0

        # Select appropriate config for this URL
        selected_config = self.select_config(url, config)

        # If no config matches, return failed result
        if selected_config is None:
            error_message = f"No matching configuration found for URL: {url}"
            if self.monitor:
                self.monitor.update_task(
                    task_id, 
                    status=CrawlStatus.FAILED,
                    error_message=error_message
                )

            return CrawlerTaskResult(
                task_id=task_id,
                url=url,
                result=CrawlResult(
                    url=url, 
                    html="", 
                    metadata={"status": "no_config_match"}, 
                    success=False, 
                    error_message=error_message
                ),
                memory_usage=0,
                peak_memory=0,
                start_time=start_time,
                end_time=time.time(),
                error_message=error_message,
                retry_count=retry_count
            )

        # Get starting memory for accurate measurement
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024 * 1024)

        try:
            if self.monitor:
                self.monitor.update_task(
                    task_id, 
                    status=CrawlStatus.IN_PROGRESS, 
                    start_time=start_time,
                    retry_count=retry_count
                )

            self.concurrent_sessions += 1

            if self.rate_limiter:
                await self.rate_limiter.wait_if_needed(url)

            # Check if we're in critical memory state
            if self.current_memory_percent >= self.critical_threshold_percent:
                # Requeue this task with increased priority and retry count
                enqueue_time = time.time()
                priority = self._get_priority_score(enqueue_time - start_time, retry_count + 1)
                await self.task_queue.put((priority, (url, task_id, retry_count + 1, enqueue_time)))

                # Update monitoring
                if self.monitor:
                    self.monitor.update_task(
                        task_id,
                        status=CrawlStatus.QUEUED,
                        error_message="Requeued due to critical memory pressure"
                    )

                # Return placeholder result with requeued status
                return CrawlerTaskResult(
                    task_id=task_id,
                    url=url,
                    result=CrawlResult(
                        url=url, html="", metadata={"status": "requeued"}, 
                        success=False, error_message="Requeued due to critical memory pressure"
                    ),
                    memory_usage=0,
                    peak_memory=0,
                    start_time=start_time,
                    end_time=time.time(),
                    error_message="Requeued due to critical memory pressure",
                    retry_count=retry_count + 1
                )

            # Execute the crawl with selected config
            result = await self.crawler.arun(url, config=selected_config, session_id=task_id)

            # Measure memory usage
            end_memory = process.memory_info().rss / (1024 * 1024)
            memory_usage = peak_memory = end_memory - start_memory

            # Handle rate limiting
            if self.rate_limiter and result.status_code:
                if not self.rate_limiter.update_delay(url, result.status_code):
                    error_message = f"Rate limit retry count exceeded for domain {urlparse(url).netloc}"
                    if self.monitor:
                        self.monitor.update_task(task_id, status=CrawlStatus.FAILED)

            # Update status based on result
            if not result.success:
                error_message = result.error_message
                if self.monitor:
                    self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
            elif self.monitor:
                self.monitor.update_task(task_id, status=CrawlStatus.COMPLETED)

        except Exception as e:
            error_message = str(e)
            if self.monitor:
                self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
            result = CrawlResult(
                url=url, html="", metadata={}, success=False, error_message=str(e)
            )

        finally:
            end_time = time.time()
            if self.monitor:
                self.monitor.update_task(
                    task_id,
                    end_time=end_time,
                    memory_usage=memory_usage,
                    peak_memory=peak_memory,
                    error_message=error_message,
                    retry_count=retry_count
                )
            self.concurrent_sessions -= 1

        return CrawlerTaskResult(
            task_id=task_id,
            url=url,
            result=result,
            memory_usage=memory_usage,
            peak_memory=peak_memory,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
            retry_count=retry_count
        )