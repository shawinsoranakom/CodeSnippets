def _serialize(
        cls,
        data: SerializableData,
        *,
        depth: int = 0,
        exclude: PropertyFilter | None = None,
        include: PropertyFilter | None = None,
        matcher: PropertyMatcher | None = None,
        path: PropertyPath = (),
        visited: set[Any] | None = None,
    ) -> str:
        """Pre-process data before serializing.

        This allows us to handle specific cases for Home Assistant data structures.
        """
        if isinstance(data, State):
            serializable_data = cls._serializable_state(data)
        elif isinstance(data, ar.AreaEntry):
            serializable_data = cls._serializable_area_registry_entry(data)
        elif isinstance(data, dr.DeviceEntry):
            serializable_data = cls._serializable_device_registry_entry(data)
        elif isinstance(data, er.RegistryEntry):
            serializable_data = cls._serializable_entity_registry_entry(data)
        elif isinstance(data, ir.IssueEntry):
            serializable_data = cls._serializable_issue_registry_entry(data)
        elif isinstance(data, dict) and "flow_id" in data and "handler" in data:
            serializable_data = cls._serializable_flow_result(data)
        elif isinstance(data, dict) and set(data) == {
            "conversation_id",
            "response",
            "continue_conversation",
        }:
            serializable_data = cls._serializable_conversation_result(data)
        elif isinstance(data, vol.Schema):
            serializable_data = voluptuous_serialize.convert(data)
        elif isinstance(data, ConfigEntry):
            serializable_data = cls._serializable_config_entry(data)
        elif dataclasses.is_dataclass(type(data)):
            serializable_data = dataclasses.asdict(data)
        elif isinstance(data, IntFlag):
            # The repr of an enum.IntFlag has changed between Python 3.10 and 3.11
            # so we normalize it here.
            serializable_data = _IntFlagWrapper(data)
        else:
            serializable_data = data
            with suppress(TypeError):
                if attr.has(type(data)):
                    serializable_data = attrs.asdict(data)

        return super()._serialize(
            serializable_data,
            depth=depth,
            exclude=exclude,
            include=include,
            matcher=matcher,
            path=path,
            visited=visited,
        )