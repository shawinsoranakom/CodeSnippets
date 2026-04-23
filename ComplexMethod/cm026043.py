async def _update_callback(self, message: Status) -> None:
        """New message from the receiver."""
        match message:
            case status.NotAvailable(kind=Kind.CHANNEL_MUTING):
                not_available = True
            case status.ChannelMuting():
                not_available = False
            case status.Power(zone=Zone.MAIN, param=status.Power.Param.ON):
                self._query_state(POWER_ON_QUERY_DELAY)
                return
            case _:
                return

        if not self._entities_added:
            _LOGGER.debug(
                "Discovered %s on %s (%s)",
                self.name,
                self.manager.info.model_name,
                self.manager.info.host,
            )
            self._entities_added = True
            async_dispatcher_send(
                self.hass,
                f"{DOMAIN}_{self.config_entry.entry_id}_channel_muting",
                self,
            )

        if not_available:
            self.data.clear()
            self._desired.clear()
            self.async_set_updated_data(self.data)
        else:
            message = cast(status.ChannelMuting, message)
            self.data = {channel: getattr(message, channel) for channel in Channel}
            self._desired = {
                channel: desired
                for channel, desired in self._desired.items()
                if self.data[channel] != desired
            }
            self.async_set_updated_data(self.data)