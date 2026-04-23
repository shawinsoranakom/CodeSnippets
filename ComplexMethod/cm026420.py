def update_devices(self, devices: list[NukiDevice]) -> dict[str, set[str]]:
        """Update the Nuki devices.

        Returns:
            A dict with the events to be fired. The event type is the key and the device ids are the value

        """

        events: dict[str, set[str]] = defaultdict(set)

        for device in devices:
            for level in (False, True):
                try:
                    if isinstance(device, NukiOpener):
                        last_ring_action_state = device.ring_action_state

                        device.update(level)

                        if not last_ring_action_state and device.ring_action_state:
                            events["ring"].add(device.nuki_id)
                    else:
                        device.update(level)
                except RequestException:
                    continue

                if device.state not in ERROR_STATES:
                    break

        return events