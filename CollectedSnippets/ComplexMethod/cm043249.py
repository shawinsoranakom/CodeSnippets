async def crawl_url(
        self,
        url: str,
        config: Union[CrawlerRunConfig, List[CrawlerRunConfig]],
        task_id: str,
        semaphore: asyncio.Semaphore = None,
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
                error_message=error_message
            )

        try:
            if self.monitor:
                self.monitor.update_task(
                    task_id, status=CrawlStatus.IN_PROGRESS, start_time=start_time
                )

            if self.rate_limiter:
                await self.rate_limiter.wait_if_needed(url)

            async with semaphore:
                process = psutil.Process()
                start_memory = process.memory_info().rss / (1024 * 1024)
                result = await self.crawler.arun(url, config=selected_config, session_id=task_id)
                end_memory = process.memory_info().rss / (1024 * 1024)

                memory_usage = peak_memory = end_memory - start_memory

                if self.rate_limiter and result.status_code:
                    if not self.rate_limiter.update_delay(url, result.status_code):
                        error_message = f"Rate limit retry count exceeded for domain {urlparse(url).netloc}"
                        if self.monitor:
                            self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
                        return CrawlerTaskResult(
                            task_id=task_id,
                            url=url,
                            result=result,
                            memory_usage=memory_usage,
                            peak_memory=peak_memory,
                            start_time=start_time,
                            end_time=time.time(),
                            error_message=error_message,
                        )

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
                )

        return CrawlerTaskResult(
            task_id=task_id,
            url=url,
            result=result,
            memory_usage=memory_usage,
            peak_memory=peak_memory,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
        )