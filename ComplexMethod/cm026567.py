def get_current_channel(self) -> FunctionalChannel:
        """Return the FunctionalChannel for the device.

        Resolution priority:
        1. For multi-channel entities with a real index, find channel by index match.
        2. For multi-channel entities without a real index, use the provided channel position.
        3. For non multi-channel entities with >1 channels, use channel at position 1
           (index 0 is often a meta/service channel in HmIP).
        Raises ValueError if no suitable channel can be resolved.
        """
        functional_channels = getattr(self._device, "functionalChannels", None)
        if not functional_channels:
            raise ValueError(
                f"Device {getattr(self._device, 'id', 'unknown')} has no functionalChannels"
            )

        # Multi-channel handling
        if self._is_multi_channel:
            # Prefer real index mapping when provided to avoid ordering issues.
            if self._channel_real_index is not None:
                for channel in functional_channels:
                    if channel.index == self._channel_real_index:
                        return channel
                raise ValueError(
                    f"Real channel index {self._channel_real_index} not found for device "
                    f"{getattr(self._device, 'id', 'unknown')}"
                )
            # Fallback: positional channel (already sorted as strings upstream).
            if self._channel is not None and 0 <= self._channel < len(
                functional_channels
            ):
                return functional_channels[self._channel]
            raise ValueError(
                f"Channel position {self._channel} invalid for device "
                f"{getattr(self._device, 'id', 'unknown')} (len={len(functional_channels)})"
            )

        # Single-channel / non multi-channel entity: choose second element if available
        if len(functional_channels) > 1:
            return functional_channels[1]
        return functional_channels[0]