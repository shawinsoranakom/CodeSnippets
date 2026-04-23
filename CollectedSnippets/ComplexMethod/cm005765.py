async def aiter_lines(self):
            if self._closed:
                return

            try:
                empty_polls = 0
                total_events = 0
                end_event_found = False

                while (
                    empty_polls < self.max_empty_polls
                    and total_events < self.max_total_events
                    and not end_event_found
                    and not self._closed
                ):
                    # Add Accept header for NDJSON
                    headers = {**self.headers, "Accept": "application/x-ndjson"}

                    try:
                        # Set a timeout for the request
                        response = await asyncio.wait_for(
                            self.client.get(
                                f"api/v1/build/{self.job_id}/events?event_delivery=polling",
                                headers=headers,
                            ),
                            timeout=self.poll_timeout,
                        )

                        if response.status_code != codes.OK:
                            break

                        # Get the NDJSON response as text
                        text = response.text

                        # Skip if response is empty
                        if not text.strip():
                            empty_polls += 1
                            await asyncio.sleep(0.1)
                            continue

                        # Reset empty polls counter since we got data
                        empty_polls = 0

                        # Process each line as an individual JSON object
                        line_count = 0
                        for line in text.splitlines():
                            if not line.strip():
                                continue

                            line_count += 1
                            total_events += 1

                            # Check for end event with multiple possible formats
                            if '"event":"end"' in line or '"event": "end"' in line:
                                end_event_found = True

                            # Validate it's proper JSON before yielding
                            try:
                                json.loads(line)  # Test parse to ensure it's valid JSON
                                yield line
                            except json.JSONDecodeError as e:
                                logger.debug(f"WARNING: Skipping invalid JSON: {line}")
                                logger.debug(f"Error: {e}")
                                # Don't yield invalid JSON, but continue processing other lines

                        # If we had no events in this batch, count as empty poll
                        if line_count == 0:
                            empty_polls += 1

                        # Add a small delay to prevent tight polling
                        await asyncio.sleep(0.1)

                    except asyncio.TimeoutError:
                        logger.debug(f"WARNING: Polling request timed out after {self.poll_timeout}s")
                        empty_polls += 1
                        continue

                # If we hit the limit without finding the end event, log a warning
                if total_events >= self.max_total_events:
                    logger.debug(
                        f"WARNING: Reached maximum event limit ({self.max_total_events}) without finding end event"
                    )

                if empty_polls >= self.max_empty_polls and not end_event_found:
                    logger.debug(
                        f"WARNING: Reached maximum empty polls ({self.max_empty_polls}) without finding end event"
                    )

            except Exception as e:
                logger.debug(f"ERROR: Unexpected error during polling: {e!s}")
                raise
            finally:
                self._closed = True