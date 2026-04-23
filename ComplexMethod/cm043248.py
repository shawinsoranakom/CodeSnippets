async def run_urls_stream(
        self,
        urls: List[str],
        crawler: AsyncWebCrawler,
        config: Union[CrawlerRunConfig, List[CrawlerRunConfig]],
    ) -> AsyncGenerator[CrawlerTaskResult, None]:
        self.crawler = crawler

        # Start the memory monitor task
        memory_monitor = asyncio.create_task(self._memory_monitor_task())

        if self.monitor:
            self.monitor.start()

        try:
            # Initialize task queue
            for url in urls:
                task_id = str(uuid.uuid4())
                if self.monitor:
                    self.monitor.add_task(task_id, url)
                # Add to queue with initial priority 0, retry count 0, and current time
                await self.task_queue.put((0, (url, task_id, 0, time.time())))

            active_tasks = []
            completed_count = 0
            total_urls = len(urls)

            while completed_count < total_urls:
                if memory_monitor.done():
                    exc = memory_monitor.exception()
                    if exc:
                        for t in active_tasks:
                            t.cancel()
                        raise exc
                # If memory pressure is low, greedily fill all available slots
                if not self.memory_pressure_mode:
                    slots = self.max_session_permit - len(active_tasks)
                    while slots > 0:
                        try:
                            # Use get_nowait() to immediately get tasks without blocking
                            priority, (url, task_id, retry_count, enqueue_time) = self.task_queue.get_nowait()

                            # Create and start the task
                            task = asyncio.create_task(
                                self.crawl_url(url, config, task_id, retry_count)
                            )
                            active_tasks.append(task)

                            # Update waiting time in monitor
                            if self.monitor:
                                wait_time = time.time() - enqueue_time
                                self.monitor.update_task(
                                    task_id, 
                                    wait_time=wait_time,
                                    status=CrawlStatus.IN_PROGRESS
                                )

                            slots -= 1

                        except asyncio.QueueEmpty:
                            # No more tasks in queue, exit the loop
                            break

                # Process completed tasks and yield results
                if active_tasks:
                    done, pending = await asyncio.wait(
                        active_tasks, timeout=0.1, return_when=asyncio.FIRST_COMPLETED
                    )

                    for completed_task in done:
                        result = await completed_task

                        # Only count as completed if it wasn't requeued
                        if "requeued" not in result.error_message:
                            completed_count += 1
                            yield result

                    # Update active tasks list
                    active_tasks = list(pending)
                else:
                    # If no active tasks but still waiting, sleep briefly
                    await asyncio.sleep(self.check_interval / 2)

                # Update priorities for waiting tasks if needed
                await self._update_queue_priorities()

        finally:
            # Clean up
            memory_monitor.cancel()
            if self.monitor:
                self.monitor.stop()