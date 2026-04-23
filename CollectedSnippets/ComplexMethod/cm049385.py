def get_devices(self):
        discovered_devices = {}
        printers = self.conn.getPrinters()
        devices = self.conn.getDevices()

        # get and adjust configuration of printers already added in cups
        for printer_name, printer in printers.items():
            path = printer.get('device-uri')
            if path and printer_name != self.get_identifier(path):
                device_class = 'direct' if 'usb' in path else 'network'
                printer.update({
                    'already-configured': True,
                    'device-class': device_class,
                    'device-make-and-model': printer_name,  # give name set in Cups
                    'device-id': '',
                })
                devices.update({printer_name: printer})

        # filter devices (both added and not added in cups) to show as detected by the IoT Box
        for path, device in devices.items():
            identifier, device = self.process_device(path, device)

            url_is_supported = any(protocol in device["url"] for protocol in ['dnssd', 'lpd', 'socket', 'ipp'])
            model_is_valid = device["device-make-and-model"] != "Unknown"
            printer_is_usb = "direct" in device["device-class"]

            if (url_is_supported and model_is_valid) or printer_is_usb:
                discovered_devices.update({identifier: device})

        # Let get_devices be called again every 20 seconds (get_devices of PrinterInterface
        # takes between 4 and 15 seconds) but increase the delay to 2 minutes if it has been
        # running for more than 1 hour
        if self.start_time and time.time() - self.start_time > 3600:
            self._loop_delay = 120
            self.start_time = None  # Reset start_time to avoid changing the loop delay again

        self.printer_devices.update(self.deduplicate_printers(discovered_devices))

        # Devices previously discovered but not found this call
        # When the printer disconnects it can still be listed in cups and print after reconnecting
        # Wait for 3 consecutive misses before removing it from the list allows us to avoid errors and unnecessary double prints
        missing = set(self.printer_devices) - set(discovered_devices)
        for identifier in missing:
            printer = self.printer_devices[identifier]
            if printer["disconnect_counter"] >= 2:
                _logger.warning('Printer %s not found 3 times in a row, disconnecting.', identifier)
                self.printer_devices.pop(identifier, None)
            else:
                printer["disconnect_counter"] += 1

        return self.printer_devices.copy()