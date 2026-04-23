def _name_internal(
        self,
        device_class_name: str | None,
        platform_translations: dict[str, str],
    ) -> str | UndefinedType | None:
        """Return the name of the entity."""
        if hasattr(self, "_attr_name"):
            return self._attr_name
        if (
            self.has_entity_name
            and (name_translation_key := self._name_translation_key)
            and (name := platform_translations.get(name_translation_key))
        ):
            return self._substitute_name_placeholders(name)
        if hasattr(self, "entity_description"):
            description_name = self.entity_description.name
            if description_name is UNDEFINED and self._default_to_device_class_name():
                return device_class_name
            return description_name

        # The entity has no name set by _attr_name, translation_key or entity_description
        # Check if the entity should be named by its device class
        if self._default_to_device_class_name():
            return device_class_name
        return UNDEFINED