def device_changed(self, device, data=None):
        """Register a new event.

        If ``data`` is provided, it means that the caller is the action method,
        it will be used as the event data (instead of the one provided by the request).

        :param Driver device: actual device class
        :param dict data: data returned by the device (optional)
        """
        data = data or (request.params.get('data', {}) if request else {})

        # Make notification available to longpolling event route
        event = {
            **device.data,
            'device_identifier': device.device_identifier,
            'time': time.time(),
            **data,
        }
        send_to_controller({
            **event,
            'iot_box_identifier': helpers.get_identifier(),
        })
        if webrtc_client:
            webrtc_client.send(event)
        self.events.append(event)
        for session in self.sessions:
            session_devices = self.sessions[session]['devices']
            if (
                any(d in [device.device_identifier, device.device_type] for d in session_devices)
                and not self.sessions[session]['event'].is_set()
            ):
                if device.device_type in session_devices:
                    event['device_identifier'] = device.device_type  # allow device type as identifier (longpolling)
                self.sessions[session]['result'] = event
                self.sessions[session]['event'].set()