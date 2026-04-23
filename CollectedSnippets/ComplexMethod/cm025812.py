async def _transformation(call: ServiceCall) -> ServiceResponse:
    """User a transformation item on a player character."""

    entry: HabiticaConfigEntry = service.async_get_config_entry(
        call.hass, DOMAIN, call.data[ATTR_CONFIG_ENTRY]
    )
    coordinator = entry.runtime_data

    item = ITEMID_MAP[call.data[ATTR_ITEM]]
    # check if target is self
    if call.data[ATTR_TARGET] in (
        str(coordinator.data.user.id),
        coordinator.data.user.profile.name,
        coordinator.data.user.auth.local.username,
    ):
        target_id = coordinator.data.user.id
    else:
        # check if target is a party member
        try:
            party = await coordinator.habitica.get_group_members(public_fields=True)
        except NotFoundError as e:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="party_not_found",
            ) from e
        except HabiticaException as e:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="service_call_exception",
                translation_placeholders={"reason": str(e.error.message)},
            ) from e
        except ClientError as e:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="service_call_exception",
                translation_placeholders={"reason": str(e)},
            ) from e
        try:
            target_id = next(
                member.id
                for member in party.data
                if member.id
                and call.data[ATTR_TARGET].lower()
                in (
                    str(member.id),
                    str(member.auth.local.username).lower(),
                    str(member.profile.name).lower(),
                )
            )
        except StopIteration as e:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="target_not_found",
                translation_placeholders={"target": f"'{call.data[ATTR_TARGET]}'"},
            ) from e
    try:
        response = await coordinator.habitica.cast_skill(item, target_id)
    except TooManyRequestsError as e:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="setup_rate_limit_exception",
            translation_placeholders={"retry_after": str(e.retry_after)},
        ) from e
    except NotAuthorizedError as e:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="item_not_found",
            translation_placeholders={"item": call.data[ATTR_ITEM]},
        ) from e
    except HabiticaException as e:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="service_call_exception",
            translation_placeholders={"reason": str(e.error.message)},
        ) from e
    except ClientError as e:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="service_call_exception",
            translation_placeholders={"reason": str(e)},
        ) from e
    else:
        return asdict(response.data)