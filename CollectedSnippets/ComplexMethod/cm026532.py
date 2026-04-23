def extra_state_attributes(self) -> dict[str, int | float | None] | None:
        """Return the state attributes of the monitored installation."""

        # Only add attributes to the original sensor
        if self.entity_description.key != "days_until_expiration":
            return None

        if self.coordinator.data is None:
            return None

        attrs = {}
        if expiration_date := self.coordinator.data.expiration_date:
            attrs[ATTR_EXPIRES] = expiration_date.isoformat()

        if name_servers := self.coordinator.data.name_servers:
            attrs[ATTR_NAME_SERVERS] = " ".join(name_servers)

        if last_updated := self.coordinator.data.last_updated:
            attrs[ATTR_UPDATED] = last_updated.isoformat()

        if registrar := self.coordinator.data.registrar:
            attrs[ATTR_REGISTRAR] = registrar

        if not attrs:
            return None

        return attrs