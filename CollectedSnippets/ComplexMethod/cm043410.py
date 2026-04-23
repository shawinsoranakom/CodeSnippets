def update_task(
        self, 
        task_id: str, 
        status: Optional[CrawlStatus] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        memory_usage: Optional[float] = None,
        peak_memory: Optional[float] = None,
        error_message: Optional[str] = None,
        retry_count: Optional[int] = None,
        wait_time: Optional[float] = None
    ):
        """
        Update statistics for a specific task.

        Args:
            task_id: Unique identifier for the task
            status: New status (QUEUED, IN_PROGRESS, COMPLETED, FAILED)
            start_time: When task execution started
            end_time: When task execution ended
            memory_usage: Current memory usage in MB
            peak_memory: Maximum memory usage in MB
            error_message: Error description if failed
            retry_count: Number of retry attempts
            wait_time: Time spent in queue

        Updates task statistics and updates status counts.
        If status changes, decrements old status count and 
        increments new status count.
        """
        with self._lock:
            # Check if task exists
            if task_id not in self.stats:
                return

            task_stats = self.stats[task_id]

            # Update status counts if status is changing
            old_status = task_stats["status"]
            if status and status.name != old_status:
                self.status_counts[old_status] -= 1
                self.status_counts[status.name] += 1

                # Track completion
                if status == CrawlStatus.COMPLETED:
                    self.urls_completed += 1

                # Track requeues
                if old_status in [CrawlStatus.COMPLETED.name, CrawlStatus.FAILED.name] and not task_stats.get("counted_requeue", False):
                    self.requeued_count += 1
                    task_stats["counted_requeue"] = True

            # Update task statistics
            if status:
                task_stats["status"] = status.name
            if start_time is not None:
                task_stats["start_time"] = start_time
            if end_time is not None:
                task_stats["end_time"] = end_time
            if memory_usage is not None:
                task_stats["memory_usage"] = memory_usage

                # Update peak memory if necessary
                current_percent = (memory_usage / psutil.virtual_memory().total) * 100
                if current_percent > self.peak_memory_percent:
                    self.peak_memory_percent = current_percent
                    self.peak_memory_time = time.time()

            if peak_memory is not None:
                task_stats["peak_memory"] = peak_memory
            if error_message is not None:
                task_stats["error_message"] = error_message
            if retry_count is not None:
                task_stats["retry_count"] = retry_count
            if wait_time is not None:
                task_stats["wait_time"] = wait_time

            # Calculate duration
            if task_stats["start_time"]:
                end = task_stats["end_time"] or time.time()
                duration = end - task_stats["start_time"]
                task_stats["duration"] = self._format_time(duration)