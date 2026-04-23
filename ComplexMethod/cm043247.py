async def _update_queue_priorities(self):
        """Periodically update priorities of items in the queue to prevent starvation"""
        # Skip if queue is empty
        if self.task_queue.empty():
            return

        # Use a drain-and-refill approach to update all priorities
        temp_items = []

        # Drain the queue (with a safety timeout to prevent blocking)
        try:
            drain_start = time.time()
            while not self.task_queue.empty() and time.time() - drain_start < 5.0:  # 5 second safety timeout
                try:
                    # Get item from queue with timeout
                    priority, (url, task_id, retry_count, enqueue_time) = await asyncio.wait_for(
                        self.task_queue.get(), timeout=0.1
                    )

                    # Calculate new priority based on current wait time
                    current_time = time.time()
                    wait_time = current_time - enqueue_time
                    new_priority = self._get_priority_score(wait_time, retry_count)

                    # Store with updated priority
                    temp_items.append((new_priority, (url, task_id, retry_count, enqueue_time)))

                    # Update monitoring stats for this task
                    if self.monitor and task_id in self.monitor.stats:
                        self.monitor.update_task(task_id, wait_time=wait_time)

                except asyncio.TimeoutError:
                    # Queue might be empty or very slow
                    break
        except Exception as e:
            # If anything goes wrong, make sure we refill the queue with what we've got
            self.monitor.update_memory_status(f"QUEUE_ERROR: {str(e)}")

        # Calculate queue statistics
        if temp_items and self.monitor:
            total_queued = len(temp_items)
            wait_times = [item[1][3] for item in temp_items]
            highest_wait_time = time.time() - min(wait_times) if wait_times else 0
            avg_wait_time = sum(time.time() - t for t in wait_times) / len(wait_times) if wait_times else 0

            # Update queue statistics in monitor
            self.monitor.update_queue_statistics(
                total_queued=total_queued,
                highest_wait_time=highest_wait_time,
                avg_wait_time=avg_wait_time
            )

        # Sort by priority (lowest number = highest priority)
        temp_items.sort(key=lambda x: x[0])

        # Refill the queue with updated priorities
        for item in temp_items:
            await self.task_queue.put(item)