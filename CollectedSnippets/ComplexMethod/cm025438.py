async def async_extract_from_service(call: ServiceCall) -> list[str]:
        if call.context.user_id:
            user = await hass.auth.async_get_user(call.context.user_id)
            if user is None:
                raise UnknownUser(context=call.context)
        else:
            user = None

        if call.data.get(ATTR_ENTITY_ID) == ENTITY_MATCH_ALL:
            # Return all entity_ids user has permission to control.
            return [
                entity_id
                for entity_id in hass.data[DATA_AMCREST][CAMERAS]
                if have_permission(user, entity_id)
            ]

        if call.data.get(ATTR_ENTITY_ID) == ENTITY_MATCH_NONE:
            return []

        call_ids = await async_extract_entity_ids(call)
        entity_ids = []
        for entity_id in hass.data[DATA_AMCREST][CAMERAS]:
            if entity_id not in call_ids:
                continue
            if not have_permission(user, entity_id):
                raise Unauthorized(
                    context=call.context, entity_id=entity_id, permission=POLICY_CONTROL
                )
            entity_ids.append(entity_id)
        return entity_ids