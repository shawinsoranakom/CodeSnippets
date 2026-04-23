async def _parse_barrier(
        self, device_type: str, barrier_state: BarrierState
    ) -> NiceGODevice | None:
        """Parse barrier data."""

        device_id = barrier_state.deviceId
        name = barrier_state.reported["displayName"]
        if barrier_state.reported["migrationStatus"] == "NOT_STARTED":
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                f"firmware_update_required_{device_id}",
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="firmware_update_required",
                translation_placeholders={"device_name": name},
            )
            return None
        ir.async_delete_issue(
            self.hass, DOMAIN, f"firmware_update_required_{device_id}"
        )
        barrier_status_raw = [
            int(x) for x in barrier_state.reported["barrierStatus"].split(",")
        ]

        if BARRIER_STATUS[int(barrier_status_raw[2])] == "STATIONARY":
            barrier_status = "open" if barrier_status_raw[0] == 1 else "closed"
        else:
            barrier_status = BARRIER_STATUS[int(barrier_status_raw[2])].lower()

        light_status = (
            barrier_state.reported["lightStatus"].split(",")[0] == "1"
            if barrier_state.reported.get("lightStatus")
            else None
        )
        fw_version = barrier_state.reported["deviceFwVersion"]
        if barrier_state.connectionState:
            connected = barrier_state.connectionState.connected
        elif device_type == "Mms100":
            connected = barrier_state.reported.get("radioConnected", 0) == 1
        else:
            # Assume connected
            connected = True
        vacation_mode = barrier_state.reported.get("vcnMode", None)

        return NiceGODevice(
            type=device_type,
            id=device_id,
            name=name,
            barrier_status=barrier_status,
            light_status=light_status,
            fw_version=fw_version,
            connected=connected,
            vacation_mode=vacation_mode,
        )