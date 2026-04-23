async def send_snapshot(self, _: datetime | None = None) -> None:
        """Send a snapshot."""
        if not self.onboarded or not self.preferences.get(ATTR_SNAPSHOTS, False):
            return

        payload = await _async_snapshot_payload(self._hass)

        if not payload:
            LOGGER.info("Skipping snapshot submission, no data to send")
            return

        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"home-assistant/{HA_VERSION}",
        }
        if self._data.submission_identifier is not None:
            headers["X-Device-Database-Submission-Identifier"] = (
                self._data.submission_identifier
            )

        url = (
            self._snapshots_url
            if self._snapshots_url is not None
            else SNAPSHOT_DEFAULT_URL
        )
        url += SNAPSHOT_URL_PATH

        try:
            async with timeout(30):
                response = await self._session.post(url, json=payload, headers=headers)

                if response.status == 200:  # OK
                    response_data = await response.json()
                    new_identifier = response_data.get("submission_identifier")

                    if (
                        new_identifier is not None
                        and new_identifier != self._data.submission_identifier
                    ):
                        self._data.submission_identifier = new_identifier
                        await self._save()

                    LOGGER.info(
                        "Submitted snapshot analytics to Home Assistant servers"
                    )

                elif response.status == 400:  # Bad Request
                    response_data = await response.json()
                    error_kind = response_data.get("kind", "unknown")
                    error_message = response_data.get("message", "Unknown error")

                    if error_kind == "invalid-submission-identifier":
                        # Clear the invalid identifier and retry on next cycle
                        LOGGER.warning(
                            "Invalid submission identifier to %s, clearing: %s",
                            url,
                            error_message,
                        )
                        self._data.submission_identifier = None
                        await self._save()
                    else:
                        LOGGER.warning(
                            "Malformed snapshot analytics submission (%s) to %s: %s",
                            error_kind,
                            url,
                            error_message,
                        )

                elif response.status == 503:  # Service Unavailable
                    response_text = await response.text()
                    LOGGER.warning(
                        "Snapshot analytics service %s unavailable: %s",
                        url,
                        response_text,
                    )

                else:
                    LOGGER.warning(
                        "Unexpected status code %s when submitting snapshot analytics to %s",
                        response.status,
                        url,
                    )

        except TimeoutError:
            LOGGER.error(
                "Timeout sending snapshot analytics to %s",
                url,
            )
        except aiohttp.ClientError as err:
            LOGGER.error(
                "Error sending snapshot analytics to %s: %r",
                url,
                err,
            )