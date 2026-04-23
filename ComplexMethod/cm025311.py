def get_device_value(
        self,
        key: str,
        subkey: str,
        qsw_type: QswEntityType | None = None,
    ) -> Any:
        """Return device value by key."""
        value = None
        if key in self.coordinator.data:
            data = self.coordinator.data[key]
            if qsw_type is not None and self.type_id is not None:
                if (
                    qsw_type in data
                    and self.type_id in data[qsw_type]
                    and subkey in data[qsw_type][self.type_id]
                ):
                    value = data[qsw_type][self.type_id][subkey]
            elif subkey in data:
                value = data[subkey]
        return value