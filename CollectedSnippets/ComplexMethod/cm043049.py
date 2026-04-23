async def send_webhook(
        self,
        webhook_url: str,
        payload: Dict,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send webhook with exponential backoff retry logic.

        Args:
            webhook_url: The URL to send the webhook to
            payload: The JSON payload to send
            headers: Optional custom headers

        Returns:
            bool: True if delivered successfully, False otherwise
        """
        default_headers = self.config.get("headers", {})
        merged_headers = {**default_headers, **(headers or {})}
        merged_headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_attempts):
                try:
                    logger.info(
                        f"Sending webhook (attempt {attempt + 1}/{self.max_attempts}) to {webhook_url}"
                    )

                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers=merged_headers
                    )

                    # Success or client error (don't retry client errors)
                    if response.status_code < 500:
                        if 200 <= response.status_code < 300:
                            logger.info(f"Webhook delivered successfully to {webhook_url}")
                            return True
                        else:
                            logger.warning(
                                f"Webhook rejected with status {response.status_code}: {response.text[:200]}"
                            )
                            return False  # Client error - don't retry

                    # Server error - retry with backoff
                    logger.warning(
                        f"Webhook failed with status {response.status_code}, will retry"
                    )

                except httpx.TimeoutException as exc:
                    logger.error(f"Webhook timeout (attempt {attempt + 1}): {exc}")
                except httpx.RequestError as exc:
                    logger.error(f"Webhook request error (attempt {attempt + 1}): {exc}")
                except Exception as exc:
                    logger.error(f"Webhook delivery error (attempt {attempt + 1}): {exc}")

                # Calculate exponential backoff delay
                if attempt < self.max_attempts - 1:
                    delay = min(self.initial_delay * (2 ** attempt), self.max_delay)
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)

        logger.error(
            f"Webhook delivery failed after {self.max_attempts} attempts to {webhook_url}"
        )
        return False