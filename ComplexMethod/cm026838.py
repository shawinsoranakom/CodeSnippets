def _async_track_service_info(
        self,
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        mac = service_info.address

        if mac in self._ignored:
            return

        if resolved := self._mac_to_irk.get(mac):
            if callbacks := self._service_info_callbacks.get(resolved):
                for cb in callbacks:
                    cb(service_info, change)
            return

        for irk, cipher in self._irks.items():
            if resolve_private_address(cipher, service_info.address):
                self._async_irk_resolved_to_mac(irk, mac)
                if callbacks := self._service_info_callbacks.get(irk):
                    for cb in callbacks:
                        cb(service_info, change)
                return

        def _unignore(service_info: bluetooth.BluetoothServiceInfoBleak) -> None:
            self._ignored.pop(service_info.address, None)

        self._ignored[mac] = bluetooth.async_track_unavailable(
            self.hass, _unignore, mac, False
        )