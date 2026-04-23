async def _async_handle_update(self, event: UpdateEvent) -> None:
        data = self.data or SystemNexa2Data()
        _is_connected = True
        match event:
            case ConnectionStatus(connected):
                _is_connected = connected
            case StateChange(state):
                data.state = state
                self._state_received_once = True
            case SettingsUpdate(settings):
                data.update_settings(settings)

        if not _is_connected:
            self.async_set_update_error(ConnectionError("No connection to device"))
        elif (
            data.on_off_settings is not None
            and self._state_received_once
            and data.state is not None
        ):
            self.async_set_updated_data(data)