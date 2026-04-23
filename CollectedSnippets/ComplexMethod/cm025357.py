def __init__(
        self,
        coordinator: ShellyRpcCoordinator,
        key: str,
        attribute: str,
        description: RpcEntityDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, key)
        self.attribute = attribute
        self.entity_description = description

        if description.role == ROLE_GENERIC:
            self._attr_name = get_rpc_channel_name(coordinator.device, key)

        self._attr_unique_id = f"{super().unique_id}-{attribute}"
        self._last_value = None
        has_id, _, component_id = get_rpc_key(key)
        self._id = int(component_id) if has_id and component_id.isnumeric() else None

        if description.unit is not None:
            self._attr_native_unit_of_measurement = description.unit(
                coordinator.device.config[key]
            )

        self.option_map: dict[str, str] = {}
        self.reversed_option_map: dict[str, str] = {}
        if "enum" in key:
            titles = self.coordinator.device.config[key]["meta"]["ui"]["titles"]
            options = self.coordinator.device.config[key]["options"]
            self.option_map = {
                opt: (titles[opt] if titles.get(opt) is not None else opt)
                for opt in options
            }
            self.reversed_option_map = {
                tit: opt for opt, tit in self.option_map.items()
            }