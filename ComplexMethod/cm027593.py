def _handle_entity_registry_updated(event: Event[Any]) -> None:
            """Handle registry create or update event."""
            if (
                event.data["action"] in {"create", "update"}
                and (entry := entity_registry.async_get(event.data["entity_id"]))
                and entry.domain == entity.platform.domain
                and entry.platform == entity.platform.platform_name
                and entry.unique_id in self.member_unique_ids
            ) or (
                event.data["action"] == "remove"
                and self._member_entity_ids is not None
                and event.data["entity_id"] in self._member_entity_ids
            ):
                if self._member_entity_ids is not None:
                    self._member_entity_ids = None
                    del self.member_entity_ids
                entity.async_write_ha_state()