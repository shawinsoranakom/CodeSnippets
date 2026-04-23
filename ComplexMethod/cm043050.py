async def notify_job_completion(
        self,
        task_id: str,
        task_type: str,
        status: str,
        urls: list,
        webhook_config: Optional[Dict],
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """
        Notify webhook of job completion.

        Args:
            task_id: The task identifier
            task_type: Type of task (e.g., "crawl", "llm_extraction")
            status: Task status ("completed" or "failed")
            urls: List of URLs that were crawled
            webhook_config: Webhook configuration from the job request
            result: Optional crawl result data
            error: Optional error message if failed
        """
        # Determine webhook URL
        webhook_url = None
        data_in_payload = self.config.get("data_in_payload", False)
        custom_headers = None

        if webhook_config:
            webhook_url = webhook_config.get("webhook_url")
            data_in_payload = webhook_config.get("webhook_data_in_payload", data_in_payload)
            custom_headers = webhook_config.get("webhook_headers")

        if not webhook_url:
            webhook_url = self.config.get("default_url")

        if not webhook_url:
            logger.debug("No webhook URL configured, skipping notification")
            return

        # Check if webhooks are enabled
        if not self.config.get("enabled", True):
            logger.debug("Webhooks are disabled, skipping notification")
            return

        # Build payload
        payload = {
            "task_id": task_id,
            "task_type": task_type,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "urls": urls
        }

        if error:
            payload["error"] = error

        if data_in_payload and result:
            payload["data"] = result

        # Send webhook (fire and forget - don't block on completion)
        await self.send_webhook(webhook_url, payload, custom_headers)