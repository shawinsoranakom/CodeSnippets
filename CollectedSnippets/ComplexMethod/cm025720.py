def __init__(
        self,
        matter_client: MatterClient,
        endpoint: MatterEndpoint,
        entity_info: MatterEntityInfo,
    ) -> None:
        """Initialize the entity."""
        self.matter_client = matter_client
        self._endpoint = endpoint
        self._entity_info = entity_info
        self.entity_description = entity_info.entity_description
        self._unsubscribes: list[Callable] = []
        # for fast lookups we create a mapping to the attribute paths
        self._attributes_map: dict[type, str] = {}
        # The server info is set when the client connects to the server.
        server_info = cast(ServerInfoMessage, self.matter_client.server_info)
        # create unique_id based on "Operational Instance Name" and endpoint/device type
        node_device_id = get_device_id(server_info, endpoint)
        self._attr_unique_id = (
            f"{node_device_id}-"
            f"{endpoint.endpoint_id}-"
            f"{entity_info.entity_description.key}-"
            f"{entity_info.primary_attribute.cluster_id}-"
            f"{entity_info.primary_attribute.attribute_id}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{ID_TYPE_DEVICE_ID}_{node_device_id}")}
        )
        self._attr_available = self._endpoint.node.available
        # mark endpoint postfix if the device has the primary attribute on multiple endpoints
        if not self._endpoint.node.is_bridge_device and any(
            ep
            for ep in self._endpoint.node.endpoints.values()
            if ep != self._endpoint
            and ep.has_attribute(None, entity_info.primary_attribute)
        ):
            self._name_postfix = str(self._endpoint.endpoint_id)
        # Always set translation_key for state_attributes translations.
        # For primary entities (no postfix), suppress the translated name,
        # so only the device name is used.
        if self._platform_translation_key and not self.translation_key:
            self._attr_translation_key = self._platform_translation_key
            if not self._name_postfix:
                self._attr_name = None

        # Matter labels can be used to modify the entity name
        # by appending the text.
        if name_modifier := self._get_name_modifier():
            self._name_postfix = name_modifier

        # make sure to update the attributes once
        self._update_from_device()