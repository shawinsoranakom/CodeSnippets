async def _async_pull_messages(self) -> None:
        """Pull messages from device."""
        if self._pullpoint_manager is None:
            return
        service = self._pullpoint_manager.get_service()
        LOGGER.debug(
            "%s: Pulling PullPoint messages timeout=%s limit=%s",
            self._name,
            PULLPOINT_POLL_TIME,
            PULLPOINT_MESSAGE_LIMIT,
        )
        next_pull_delay = None
        response = None
        try:
            if self._hass.is_running:
                response = await service.PullMessages(
                    {
                        "MessageLimit": PULLPOINT_MESSAGE_LIMIT,
                        "Timeout": PULLPOINT_POLL_TIME,
                    }
                )
            else:
                LOGGER.debug(
                    "%s: PullPoint skipped because Home Assistant is not running yet",
                    self._name,
                )
        except aiohttp.ServerDisconnectedError as err:
            # Either a shutdown event or the camera closed the connection. Because
            # http://datatracker.ietf.org/doc/html/rfc2616#section-8.1.4 allows the server
            # to close the connection at any time, we treat this as a normal. Some
            # cameras may close the connection if there are no messages to pull.
            LOGGER.debug(
                "%s: PullPoint subscription encountered a server disconnected error "
                "(this is normal for some cameras): %s",
                self._name,
                stringify_onvif_error(err),
            )
        except Fault as err:
            # Device may not support subscriptions so log at debug level
            # when we get an XMLParseError
            LOGGER.debug(
                "%s: Failed to fetch PullPoint subscription messages: %s",
                self._name,
                stringify_onvif_error(err),
            )
            # Treat errors as if the camera restarted. Assume that the pullpoint
            # subscription is no longer valid.
            self._pullpoint_manager.resume()
        except (
            XMLParseError,
            aiohttp.ClientError,
            TimeoutError,
            TransportError,
        ) as err:
            LOGGER.debug(
                "%s: PullPoint subscription encountered an unexpected error and will be retried "
                "(this is normal for some cameras): %s",
                self._name,
                stringify_onvif_error(err),
            )
            # Avoid renewing the subscription too often since it causes problems
            # for some cameras, mainly the Tapo ones.
            next_pull_delay = SUBSCRIPTION_RESTART_INTERVAL_ON_ERROR
        finally:
            self.async_schedule_pull_messages(next_pull_delay)

        if self.state != PullPointManagerState.STARTED:
            # If the webhook became started working during the long poll,
            # and we got paused, our data is stale and we should not process it.
            LOGGER.debug(
                "%s: PullPoint state is %s (likely due to working webhook), skipping PullPoint messages",
                self._name,
                self.state,
            )
            return

        if not response:
            return

        # Parse response
        event_manager = self._event_manager
        if (notification_message := response.NotificationMessage) and (
            number_of_events := len(notification_message)
        ):
            LOGGER.debug(
                "%s: continuous PullMessages: %s event(s)",
                self._name,
                number_of_events,
            )
            await event_manager.async_parse_messages(notification_message)
            event_manager.async_callback_listeners()
        else:
            LOGGER.debug("%s: continuous PullMessages: no events", self._name)