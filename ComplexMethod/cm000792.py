async def generate_video(
        self, input_data: Input, credentials: FalCredentials
    ) -> str:
        """Generate video using the specified FAL model."""
        base_url = "https://queue.fal.run"
        api_key = credentials.api_key.get_secret_value()
        headers = self._get_headers(api_key)

        # Submit generation request
        submit_url = f"{base_url}/{input_data.model.value}"
        submit_data = {"prompt": input_data.prompt}
        if input_data.model == FalModel.VEO3:
            submit_data["generate_audio"] = True  # type: ignore

        seen_logs = set()

        try:
            # Submit request to queue
            submit_response = await Requests().post(
                submit_url, headers=headers, json=submit_data
            )
            request_data = submit_response.json()

            # Get request_id and urls from initial response
            request_id = request_data.get("request_id")
            status_url = request_data.get("status_url")
            result_url = request_data.get("response_url")

            if not all([request_id, status_url, result_url]):
                raise ValueError("Missing required data in submission response")

            # Ensure status_url is a string
            if not isinstance(status_url, str):
                raise ValueError("Invalid status URL format")

            # Ensure result_url is a string
            if not isinstance(result_url, str):
                raise ValueError("Invalid result URL format")

            # Poll for status with exponential backoff
            max_attempts = 30
            attempt = 0
            base_wait_time = 5

            while attempt < max_attempts:
                status_response = await Requests().get(
                    f"{status_url}?logs=1", headers=headers
                )
                status_data = status_response.json()

                # Process new logs only
                logs = status_data.get("logs", [])
                if logs and isinstance(logs, list):
                    for log in logs:
                        if isinstance(log, dict):
                            # Create a unique key for this log entry
                            log_key = (
                                f"{log.get('timestamp', '')}-{log.get('message', '')}"
                            )
                            if log_key not in seen_logs:
                                seen_logs.add(log_key)
                                message = log.get("message", "")
                                if message:
                                    logger.debug(
                                        f"[FAL Generation] [{log.get('level', 'INFO')}] [{log.get('source', '')}] [{log.get('timestamp', '')}] {message}"
                                    )

                status = status_data.get("status")
                if status == "COMPLETED":
                    # Get the final result
                    result_response = await Requests().get(result_url, headers=headers)
                    result_data = result_response.json()

                    if "video" not in result_data or not isinstance(
                        result_data["video"], dict
                    ):
                        raise ValueError("Invalid response format - missing video data")

                    video_url = result_data["video"].get("url")
                    if not video_url or not isinstance(video_url, str):
                        raise ValueError("No valid video URL in response")

                    return video_url

                elif status == "FAILED":
                    error_msg = status_data.get("error", "No error details provided")
                    raise RuntimeError(f"Video generation failed: {error_msg}")
                elif status == "IN_QUEUE":
                    position = status_data.get("queue_position", "unknown")
                    logger.debug(
                        f"[FAL Generation] Status: In queue, position: {position}"
                    )
                elif status == "IN_PROGRESS":
                    logger.debug(
                        "[FAL Generation] Status: Request is being processed..."
                    )
                else:
                    logger.info(f"[FAL Generation] Status: Unknown status: {status}")

                wait_time = min(base_wait_time * (2**attempt), 60)  # Cap at 60 seconds
                await asyncio.sleep(wait_time)
                attempt += 1

            raise RuntimeError("Maximum polling attempts reached")

        except ClientResponseError as e:
            raise RuntimeError(f"API request failed: {str(e)}")