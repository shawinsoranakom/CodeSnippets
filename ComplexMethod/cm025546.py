async def _async_process_ports(self, usb_devices: Sequence[USBDevice]) -> None:
        """Process each discovered port."""
        _LOGGER.debug("USB devices: %r", usb_devices)

        # CP2102N chips create *two* serial ports on macOS: `/dev/cu.usbserial-` and
        # `/dev/cu.SLAB_USBtoUART*`. The former does not work and we should ignore them.
        if sys.platform == "darwin":
            silabs_serials = {
                dev.serial_number
                for dev in usb_devices
                if dev.device.startswith("/dev/cu.SLAB_USBtoUART")
            }

            filtered_usb_devices = {
                dev
                for dev in usb_devices
                if dev.serial_number not in silabs_serials
                or (
                    dev.serial_number in silabs_serials
                    and dev.device.startswith("/dev/cu.SLAB_USBtoUART")
                )
            }
        else:
            filtered_usb_devices = set(usb_devices)

        added_devices = filtered_usb_devices - self._last_processed_devices
        removed_devices = self._last_processed_devices - filtered_usb_devices
        self._last_processed_devices = filtered_usb_devices

        _LOGGER.debug(
            "Added devices: %r, removed devices: %r", added_devices, removed_devices
        )

        if added_devices or removed_devices:
            for callback in self._port_event_callbacks.copy():
                try:
                    callback(added_devices, removed_devices)
                except Exception:
                    _LOGGER.exception("Error in USB port event callback")

        for usb_device in removed_devices:
            await self._async_process_removed_usb_device(usb_device)

        for usb_device in added_devices:
            await self._async_process_discovered_usb_device(usb_device)