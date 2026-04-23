def __init__(self, entity_data: EntityData, *args, **kwargs) -> None:
        """Init ZHA entity."""
        super().__init__(*args, **kwargs)
        self.entity_data: EntityData = entity_data
        self._unsubs: list[Callable[[], None]] = []

        if self.entity_data.entity.icon is not None:
            # Only custom quirks will realistically set an icon
            self._attr_icon = self.entity_data.entity.icon

        meta = self.entity_data.entity.info_object
        self._attr_unique_id = meta.unique_id

        if self.entity_data.is_group_entity:
            group_proxy = self.entity_data.group_proxy
            assert group_proxy is not None
            platform = self.entity_data.entity.PLATFORM
            unique_ids = [
                entity.info_object.unique_id
                for member in group_proxy.group.members
                for entity in member.associated_entities
                if platform == entity.PLATFORM
            ]
            self.group = IntegrationSpecificGroup(self, unique_ids)

        if meta.entity_category is not None:
            self._attr_entity_category = EntityCategory(meta.entity_category)

        self._attr_entity_registry_enabled_default = (
            meta.entity_registry_enabled_default
        )

        if meta.translation_key is not None:
            self._attr_translation_key = meta.translation_key

        if meta.translation_placeholders is not None:
            self._attr_translation_placeholders = meta.translation_placeholders