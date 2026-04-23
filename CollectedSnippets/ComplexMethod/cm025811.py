async def _score_task(call: ServiceCall) -> ServiceResponse:
    """Score a task action."""
    entry: HabiticaConfigEntry = service.async_get_config_entry(
        call.hass, DOMAIN, call.data[ATTR_CONFIG_ENTRY]
    )
    coordinator = entry.runtime_data

    direction = (
        Direction.DOWN if call.data.get(ATTR_DIRECTION) == "down" else Direction.UP
    )
    try:
        task_id, task_value = next(
            (task.id, task.value)
            for task in coordinator.data.tasks
            if call.data[ATTR_TASK] in (str(task.id), task.alias, task.text)
        )
    except StopIteration as e:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="task_not_found",
            translation_placeholders={"task": f"'{call.data[ATTR_TASK]}'"},
        ) from e

    if TYPE_CHECKING:
        assert task_id
    try:
        response = await coordinator.habitica.update_score(task_id, direction)
    except TooManyRequestsError as e:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="setup_rate_limit_exception",
            translation_placeholders={"retry_after": str(e.retry_after)},
        ) from e
    except NotAuthorizedError as e:
        if task_value is not None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="not_enough_gold",
                translation_placeholders={
                    "gold": f"{(coordinator.data.user.stats.gp or 0):.2f} GP",
                    "cost": f"{task_value:.2f} GP",
                },
            ) from e
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="service_call_exception",
            translation_placeholders={"reason": e.error.message},
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