def get_updates(self) -> dict[str, Any]:
        """Fetch data from Yale."""
        try:
            arm_status = self.yale.get_armed_status()
            data = self.yale.get_information()
            if TYPE_CHECKING:
                assert data.cycle
            for device in data.cycle["data"]["device_status"]:
                if device["type"] == YaleLock.DEVICE_TYPE:
                    for lock in self.locks:
                        if lock.name == device["name"]:
                            lock.update(device)
        except AuthenticationError as error:
            raise ConfigEntryAuthFailed from error
        except YALE_BASE_ERRORS as error:
            raise UpdateFailed from error

        cycle = data.cycle["data"] if data.cycle else None
        status = data.status["data"] if data.status else None
        online = data.online["data"] if data.online else None
        panel_info = data.panel_info["data"] if data.panel_info else None

        return {
            "arm_status": arm_status,
            "cycle": cycle,
            "status": status,
            "online": online,
            "panel_info": panel_info,
        }