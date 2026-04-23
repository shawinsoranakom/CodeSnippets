def available(self) -> bool:
        """Return True if entity is available."""
        external_usb = self._api.external_usb
        assert external_usb is not None
        if "device" in self.entity_description.key:
            for device in external_usb.get_devices.values():
                if device.device_name == self._device_id:
                    return super().available
        elif "partition" in self.entity_description.key:
            for device in external_usb.get_devices.values():
                for partition in device.device_partitions.values():
                    if partition.partition_title == self._device_id:
                        return super().available
        return False