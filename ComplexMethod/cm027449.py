def native_value(self) -> StateType:
        """Return the state."""
        external_usb = self._api.external_usb
        if TYPE_CHECKING:
            assert external_usb is not None
        if "device" in self.entity_description.key:
            for device in external_usb.get_devices.values():
                if device.device_name == self._device_id:
                    attr = getattr(device, self.entity_description.key)
                    break
        elif "partition" in self.entity_description.key:
            for device in external_usb.get_devices.values():
                for partition in device.device_partitions.values():
                    if partition.partition_title == self._device_id:
                        attr = getattr(partition, self.entity_description.key)
                        break
        if callable(attr):
            attr = attr()
        if attr is None:
            return None

        return attr