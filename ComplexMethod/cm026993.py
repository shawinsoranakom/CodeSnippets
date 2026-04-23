def generate_name(
        self,
        include_value_name: bool = False,
        alternate_value_name: str | None = None,
        additional_info: Sequence[str | None] | None = None,
        name_prefix: str | None = None,
    ) -> str:
        """Generate entity name."""
        primary_value = self.info.primary_value
        name = ""
        if (
            hasattr(self, "entity_description")
            and self.entity_description
            and self.entity_description.name
            and self.entity_description.name is not UNDEFINED
        ):
            name = self.entity_description.name

        if name_prefix:
            name = f"{name_prefix} {name}".strip()

        value_name = ""
        if alternate_value_name:
            value_name = alternate_value_name
        elif include_value_name:
            value_name = (
                primary_value.metadata.label
                or primary_value.property_key_name
                or primary_value.property_name
                or ""
            )

        name = f"{name} {value_name}".strip()
        # Only include non empty additional info
        if additional_info := [item for item in (additional_info or []) if item]:
            name = f"{name} {' '.join(additional_info)}"

        # Only append endpoint to name if there are equivalent values on a lower
        # endpoint
        if primary_value.endpoint is not None and any(
            get_value_id_str(
                self.info.node,
                primary_value.command_class,
                primary_value.property_,
                endpoint=endpoint_idx,
                property_key=primary_value.property_key,
            )
            in self.info.node.values
            for endpoint_idx in range(primary_value.endpoint)
        ):
            name += f" ({primary_value.endpoint})"

        return name.strip()