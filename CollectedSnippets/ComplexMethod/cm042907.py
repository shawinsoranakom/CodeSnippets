def update_queue_stats(monitor, num_queued_tasks):
    """Update queue statistics periodically."""
    while monitor.is_running:
        queued_tasks = [
            task for task_id, task in monitor.get_all_task_stats().items()
            if task["status"] == CrawlStatus.QUEUED.name
        ]

        total_queued = len(queued_tasks)

        if total_queued > 0:
            current_time = time.time()
            wait_times = [
                current_time - task.get("enqueue_time", current_time)
                for task in queued_tasks
            ]
            highest_wait_time = max(wait_times) if wait_times else 0.0
            avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0.0
        else:
            highest_wait_time = 0.0
            avg_wait_time = 0.0

        monitor.update_queue_statistics(
            total_queued=total_queued,
            highest_wait_time=highest_wait_time,
            avg_wait_time=avg_wait_time
        )

        # Simulate memory pressure based on number of active tasks
        active_tasks = len([
            task for task_id, task in monitor.get_all_task_stats().items()
            if task["status"] == CrawlStatus.IN_PROGRESS.name
        ])

        if active_tasks > 8:
            monitor.update_memory_status("CRITICAL")
        elif active_tasks > 4:
            monitor.update_memory_status("PRESSURE")
        else:
            monitor.update_memory_status("NORMAL")

        time.sleep(1.0)