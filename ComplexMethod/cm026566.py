def name(self) -> str:
        """Return the name of the generic entity."""

        name = ""
        # Try to get a label from a channel.
        functional_channels = getattr(self._device, "functionalChannels", None)
        if functional_channels and self.functional_channel:
            if self._is_multi_channel:
                label = getattr(self.functional_channel, "label", None)
                if label:
                    name = str(label)
            elif len(functional_channels) > 1:
                label = getattr(functional_channels[1], "label", None)
                if label:
                    name = str(label)

        # Use device label, if name is not defined by channel label.
        if not name:
            name = self._device.label or ""
            if self._post:
                name = f"{name} {self._post}"
            elif self._is_multi_channel:
                name = f"{name} Channel{self.get_channel_index()}"

        # Add a prefix to the name if the homematic ip home has a name.
        home_name = getattr(self._home, "name", None)
        if name and home_name:
            name = f"{home_name} {name}"

        return name