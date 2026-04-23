def get_summary(self) -> Dict:
        """
        Get a summary of all crawler statistics.

        Returns:
            Dictionary containing:
            - runtime: Total runtime in seconds
            - urls_total: Total URLs to process
            - urls_completed: Number of completed URLs
            - completion_percentage: Percentage complete
            - status_counts: Count of tasks in each status
            - memory_status: Current memory status
            - peak_memory_percent: Highest memory usage
            - peak_memory_time: When peak memory occurred
            - avg_task_duration: Average task processing time
            - estimated_completion_time: Projected finish time
            - requeue_rate: Percentage of tasks requeued
        """
        with self._lock:
            # Calculate runtime
            current_time = time.time()
            runtime = current_time - (self.start_time or current_time)

            # Calculate completion percentage
            completion_percentage = 0
            if self.urls_total > 0:
                completion_percentage = (self.urls_completed / self.urls_total) * 100

            # Calculate average task duration for completed tasks
            completed_tasks = [
                task for task in self.stats.values() 
                if task["status"] == CrawlStatus.COMPLETED.name and task.get("start_time") and task.get("end_time")
            ]

            avg_task_duration = 0
            if completed_tasks:
                total_duration = sum(task["end_time"] - task["start_time"] for task in completed_tasks)
                avg_task_duration = total_duration / len(completed_tasks)

            # Calculate requeue rate
            requeue_rate = 0
            if len(self.stats) > 0:
                requeue_rate = (self.requeued_count / len(self.stats)) * 100

            # Calculate estimated completion time
            estimated_completion_time = "N/A"
            if avg_task_duration > 0 and self.urls_total > 0 and self.urls_completed > 0:
                remaining_tasks = self.urls_total - self.urls_completed
                estimated_seconds = remaining_tasks * avg_task_duration
                estimated_completion_time = self._format_time(estimated_seconds)

            return {
                "runtime": runtime,
                "urls_total": self.urls_total,
                "urls_completed": self.urls_completed,
                "completion_percentage": completion_percentage,
                "status_counts": self.status_counts.copy(),
                "memory_status": self.memory_status,
                "peak_memory_percent": self.peak_memory_percent,
                "peak_memory_time": self.peak_memory_time,
                "avg_task_duration": avg_task_duration,
                "estimated_completion_time": estimated_completion_time,
                "requeue_rate": requeue_rate,
                "requeued_count": self.requeued_count
            }