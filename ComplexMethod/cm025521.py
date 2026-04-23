def router_entity(router: SmButtonDescription, idx: int) -> None:
            nonlocal entity_created
            zb_type = coordinator.data.info.radios[idx].zb_type

            if zb_type == 1 and not entity_created[idx]:
                async_add_entities([SmButton(coordinator, router, idx)])
                entity_created[idx] = True
            elif zb_type != 1 and (startup or entity_created[idx]):
                entity_registry = er.async_get(hass)
                button = f"_{idx}" if idx else ""
                if entity_id := entity_registry.async_get_entity_id(
                    BUTTON_DOMAIN,
                    DOMAIN,
                    f"{coordinator.unique_id}-{router.key}{button}",
                ):
                    entity_registry.async_remove(entity_id)