async def groups_service_handler(service: ServiceCall) -> None:
        """Handle dynamic group service functions."""
        object_id = service.data[ATTR_OBJECT_ID]
        entity_id = f"{DOMAIN}.{object_id}"
        group = component.get_entity(entity_id)

        # new group
        if service.service == SERVICE_SET and group is None:
            entity_ids = (
                service.data.get(ATTR_ENTITIES)
                or service.data.get(ATTR_ADD_ENTITIES)
                or None
            )

            await Group.async_create_group(
                hass,
                service.data.get(ATTR_NAME, object_id),
                created_by_service=True,
                entity_ids=entity_ids,
                icon=service.data.get(ATTR_ICON),
                mode=service.data.get(ATTR_ALL),
                object_id=object_id,
                order=None,
            )
            return

        if group is None:
            _LOGGER.warning("%s:Group '%s' doesn't exist!", service.service, object_id)
            return

        # update group
        if service.service == SERVICE_SET:
            need_update = False

            if ATTR_ADD_ENTITIES in service.data:
                delta = service.data[ATTR_ADD_ENTITIES]
                entity_ids = set(group.tracking) | set(delta)
                group.async_update_tracked_entity_ids(entity_ids)

            if ATTR_REMOVE_ENTITIES in service.data:
                delta = service.data[ATTR_REMOVE_ENTITIES]
                entity_ids = set(group.tracking) - set(delta)
                group.async_update_tracked_entity_ids(entity_ids)

            if ATTR_ENTITIES in service.data:
                entity_ids = service.data[ATTR_ENTITIES]
                group.async_update_tracked_entity_ids(entity_ids)

            if ATTR_NAME in service.data:
                group.set_name(service.data[ATTR_NAME])
                need_update = True

            if ATTR_ICON in service.data:
                group.set_icon(service.data[ATTR_ICON])
                need_update = True

            if ATTR_ALL in service.data:
                group.mode = all if service.data[ATTR_ALL] else any
                need_update = True

            if need_update:
                group.async_write_ha_state()

            return

        # remove group
        if service.service == SERVICE_REMOVE:
            await component.async_remove_entity(entity_id)