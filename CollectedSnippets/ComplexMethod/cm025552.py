def __init__(self, entry: AndroidTVConfigEntry) -> None:
        """Initialize the AndroidTV base entity."""
        self.aftv = entry.runtime_data.aftv
        self._attr_unique_id = entry.unique_id
        self._entry_runtime_data = entry.runtime_data

        device_class = self.aftv.DEVICE_CLASS
        device_type = (
            PREFIX_ANDROIDTV if device_class == DEVICE_ANDROIDTV else PREFIX_FIRETV
        )
        # CONF_NAME may be present in entry.data for configuration imported from YAML
        device_name = entry.data.get(
            CONF_NAME, f"{device_type} {entry.data[CONF_HOST]}"
        )
        info = self.aftv.device_properties
        model = info.get(ATTR_MODEL)
        self._attr_device_info = DeviceInfo(
            model=f"{model} ({device_type})" if model else device_type,
            name=device_name,
        )
        if self.unique_id:
            self._attr_device_info[ATTR_IDENTIFIERS] = {(DOMAIN, self.unique_id)}
        if manufacturer := info.get(ATTR_MANUFACTURER):
            self._attr_device_info[ATTR_MANUFACTURER] = manufacturer
        if sw_version := info.get(ATTR_SW_VERSION):
            self._attr_device_info[ATTR_SW_VERSION] = sw_version
        if mac := get_androidtv_mac(info):
            self._attr_device_info[ATTR_CONNECTIONS] = {(CONNECTION_NETWORK_MAC, mac)}

        # ADB exceptions to catch
        if not self.aftv.adb_server_ip:
            # Using "adb_shell" (Python ADB implementation)
            self.exceptions = ADB_PYTHON_EXCEPTIONS
        else:
            # Communicate via ADB server
            self.exceptions = ADB_TCP_EXCEPTIONS