def ws_list_item(
        self, hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
    ) -> None:
        """List items specifically for tag.

        Provides name from entity_registry instead of storage collection.
        """
        tag_items = []
        for item in self.storage_collection.async_items():
            # Make a copy to avoid adding name to the stored entry
            item = {k: v for k, v in item.items() if k != "migrated"}
            if (
                entity_id := self.entity_registry.async_get_entity_id(
                    DOMAIN, DOMAIN, item[CONF_ID]
                )
            ) and (entity := self.entity_registry.async_get(entity_id)):
                item[CONF_NAME] = entity.name or entity.original_name
            tag_items.append(item)
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("Listing tags %s", tag_items)
        connection.send_result(msg["id"], tag_items)