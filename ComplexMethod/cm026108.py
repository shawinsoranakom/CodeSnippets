def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the fan."""
        attr: dict[str, Any] = {}

        if hasattr(self.device.state, "active_time"):
            attr["active_time"] = self.device.state.active_time

        if (
            hasattr(self.device.state, "display_status")
            and self.device.state.display_status is not None
        ):
            attr["display_status"] = getattr(
                self.device.state.display_status, "value", None
            )

        if (
            hasattr(self.device.state, "child_lock")
            and self.device.state.child_lock is not None
        ):
            attr["child_lock"] = self.device.state.child_lock

        if (
            hasattr(self.device.state, "nightlight_status")
            and self.device.state.nightlight_status is not None
        ):
            attr["night_light"] = getattr(
                self.device.state.nightlight_status, "value", None
            )
        if hasattr(self.device.state, "mode"):
            attr["mode"] = self.device.state.mode

        return attr