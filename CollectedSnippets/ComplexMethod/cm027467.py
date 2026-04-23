async def ws_connect(self) -> None:
        """Connect websocket."""
        while True:
            try:
                if self._ws and (exc := self._ws.exception()):
                    raise exc  # noqa: TRY301
            except asyncio.InvalidStateError:
                self._attr_available = True
            except asyncio.CancelledError:
                self._attr_available = False
                return
            except NtfyForbiddenError:
                if self._attr_available:
                    _LOGGER.error(
                        "Failed to subscribe to topic %s. Topic is protected",
                        self.topic,
                    )
                self._attr_available = False
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    f"topic_protected_{self.topic}",
                    is_fixable=True,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="topic_protected",
                    translation_placeholders={CONF_TOPIC: self.topic},
                    data={"entity_id": self.entity_id, "topic": self.topic},
                )
                return
            except NtfyHTTPError as e:
                if self._attr_available:
                    _LOGGER.error(
                        "Failed to connect to ntfy service due to a server error: %s (%s)",
                        e.error,
                        e.link,
                    )
                self._attr_available = False
            except NtfyConnectionError:
                if self._attr_available:
                    _LOGGER.error(
                        "Failed to connect to ntfy service due to a connection error"
                    )
                self._attr_available = False
            except NtfyTimeoutError:
                if self._attr_available:
                    _LOGGER.error(
                        "Failed to connect to ntfy service due to a connection timeout"
                    )
                self._attr_available = False
            except Exception:
                if self._attr_available:
                    _LOGGER.exception(
                        "Failed to connect to ntfy service due to an unexpected exception"
                    )
                self._attr_available = False
            finally:
                self.async_write_ha_state()
            if self._ws is None or self._ws.done():
                self._ws = self.config_entry.async_create_background_task(
                    self.hass,
                    target=self.ntfy.subscribe(
                        topics=[self.topic],
                        callback=self._async_handle_event,
                        title=self.subentry.data.get(CONF_TITLE),
                        message=self.subentry.data.get(CONF_MESSAGE),
                        priority=self.subentry.data.get(CONF_PRIORITY),
                        tags=self.subentry.data.get(CONF_TAGS),
                    ),
                    name="ntfy_websocket",
                )
            await asyncio.sleep(RECONNECT_INTERVAL)