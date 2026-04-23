async def _cast_skill(call: ServiceCall) -> ServiceResponse:
    """Skill action."""
    entry: HabiticaConfigEntry = service.async_get_config_entry(
        call.hass, DOMAIN, call.data[ATTR_CONFIG_ENTRY]
    )
    coordinator = entry.runtime_data

    skill = SKILL_MAP[call.data[ATTR_SKILL]]
    cost = COST_MAP[call.data[ATTR_SKILL]]

    try:
        task_id = next(
            task.id
            for task in coordinator.data.tasks
            if call.data[ATTR_TASK] in (str(task.id), task.alias, task.text)
        )
    except StopIteration as e:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="task_not_found",
            translation_placeholders={"task": f"'{call.data[ATTR_TASK]}'"},
        ) from e

    try:
        response = await coordinator.habitica.cast_skill(skill, task_id)
    except TooManyRequestsError as e:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="setup_rate_limit_exception",
            translation_placeholders={"retry_after": str(e.retry_after)},
        ) from e
    except NotAuthorizedError as e:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="not_enough_mana",
            translation_placeholders={
                "cost": cost,
                "mana": f"{int(coordinator.data.user.stats.mp or 0)} MP",
            },
        ) from e
    except NotFoundError as e:
        # could also be task not found, but the task is looked up
        # before the request, so most likely wrong skill selected
        # or the skill hasn't been unlocked yet.
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="skill_not_found",
            translation_placeholders={"skill": call.data[ATTR_SKILL]},
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
        await coordinator.async_request_refresh()
        return asdict(response.data)