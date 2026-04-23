def update_task(self, task_id: str, **kwargs):
        # Track URL status changes for test results
        if task_id in self.stats:
            old_status = self.stats[task_id].status

            # If this is a requeue event (requeued due to memory pressure)
            if 'error_message' in kwargs and 'requeued' in kwargs['error_message']:
                if not hasattr(self.stats[task_id], 'counted_requeue') or not self.stats[task_id].counted_requeue:
                    self.test_results.requeued_count += 1
                    self.stats[task_id].counted_requeue = True

            # Track completion status for test results
            if 'status' in kwargs:
                new_status = kwargs['status']
                if old_status != new_status:
                    if new_status == CrawlStatus.COMPLETED:
                        if task_id not in self.test_results.completed_urls:
                            self.test_results.completed_urls.append(task_id)
                    elif new_status == CrawlStatus.FAILED:
                        if task_id not in self.test_results.failed_urls:
                            self.test_results.failed_urls.append(task_id)

        # Call parent method to update the dashboard
        super().update_task(task_id, **kwargs)
        self.live.update(self._create_table())