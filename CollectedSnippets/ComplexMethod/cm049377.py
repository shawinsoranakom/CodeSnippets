def add_device(self, identifier, device):
        if identifier in iot_devices:
            return
        supported_driver = next(
            (driver for driver in self.drivers if driver.supported(device)),
            None
        )
        if supported_driver:
            _logger.info('Device %s is now connected', identifier)
            if identifier in unsupported_devices:
                del unsupported_devices[identifier]
            d = supported_driver(identifier, device)
            iot_devices[identifier] = d
            # Start the thread after creating the iot_devices entry so the
            # thread can assume the iot_devices entry will exist while it's
            # running, at least until the `disconnect` above gets triggered
            # when `removed` is not empty.
            d.start()
        elif self.allow_unsupported and identifier not in unsupported_devices:
            _logger.info('Unsupported device %s is now connected', identifier)
            unsupported_devices[identifier] = {
                'name': f'Unknown device ({self.connection_type})',
                'identifier': identifier,
                'type': 'unsupported',
                'connection': 'direct' if self.connection_type == 'usb' else self.connection_type,
            }