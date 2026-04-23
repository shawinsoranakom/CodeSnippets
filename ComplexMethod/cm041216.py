def _serialize_type_structure(
        self,
        serialized: bytearray,
        value: dict,
        shape: Shape | None,
        name: str | None = None,
        shape_members: dict[str, Shape] | None = None,
    ) -> None:
        # `_serialize_type_structure` has a different signature other `_serialize_type_*` methods as it accepts
        # `shape_members`. This is because sometimes, the `StructureShape` does not have some members defined in the
        # specs, and we want to be able to pass arbitrary members to serialize undocumented members.
        # see `_serialize_error_structure` for its specific usage

        if name is not None:
            # For nested structures, we need to serialize the key first
            self._serialize_data_item(serialized, name, shape.key_shape)

        # Remove `None` values from the dictionary
        value = {k: v for k, v in value.items() if v is not None}

        initial_bytes, closing_bytes = self._get_bytes_for_data_structure(
            value, self.MAP_MAJOR_TYPE
        )
        serialized.extend(initial_bytes)
        members = shape_members or shape.members
        for member_key, member_value in value.items():
            member_shape = members[member_key]
            if "name" in member_shape.serialization:
                member_key = member_shape.serialization["name"]
            if member_value is not None:
                self._serialize_type_string(serialized, member_key, None, None)
                self._serialize_data_item(serialized, member_value, member_shape)

        if closing_bytes is not None:
            serialized.extend(closing_bytes)