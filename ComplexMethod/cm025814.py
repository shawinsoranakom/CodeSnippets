async def _create_or_update_task(call: ServiceCall) -> ServiceResponse:  # noqa: C901
    """Create or update task action."""
    entry: HabiticaConfigEntry = service.async_get_config_entry(
        call.hass, DOMAIN, call.data[ATTR_CONFIG_ENTRY]
    )
    coordinator = entry.runtime_data
    await coordinator.async_refresh()
    is_update = call.service in (
        SERVICE_UPDATE_HABIT,
        SERVICE_UPDATE_REWARD,
        SERVICE_UPDATE_TODO,
        SERVICE_UPDATE_DAILY,
    )
    task_type = SERVICE_TASK_TYPE_MAP[call.service]
    current_task = None

    if is_update:
        try:
            current_task = next(
                task
                for task in coordinator.data.tasks
                if call.data[ATTR_TASK] in (str(task.id), task.alias, task.text)
                and task.Type is task_type
            )
        except StopIteration as e:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="task_not_found",
                translation_placeholders={"task": f"'{call.data[ATTR_TASK]}'"},
            ) from e

    data = Task()

    if not is_update:
        data["type"] = task_type

    if (text := call.data.get(ATTR_RENAME)) or (text := call.data.get(ATTR_NAME)):
        data["text"] = text

    if (notes := call.data.get(ATTR_NOTES)) is not None:
        data["notes"] = notes

    tags = cast(list[str], call.data.get(ATTR_TAG))
    remove_tags = cast(list[str], call.data.get(ATTR_REMOVE_TAG))

    if tags or remove_tags:
        update_tags = set(current_task.tags) if current_task else set()
        user_tags = {
            tag.name.lower(): tag.id
            for tag in coordinator.data.user.tags
            if tag.id and tag.name
        }

        if tags:
            # Creates new tag if it doesn't exist
            async def create_tag(tag_name: str) -> UUID:
                tag_id = (await coordinator.habitica.create_tag(tag_name)).data.id
                if TYPE_CHECKING:
                    assert tag_id
                return tag_id

            try:
                update_tags.update(
                    {
                        user_tags.get(tag_name.lower()) or (await create_tag(tag_name))
                        for tag_name in tags
                    }
                )
            except TooManyRequestsError as e:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="setup_rate_limit_exception",
                    translation_placeholders={"retry_after": str(e.retry_after)},
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

        if remove_tags:
            update_tags.difference_update(
                {
                    user_tags[tag_name.lower()]
                    for tag_name in remove_tags
                    if tag_name.lower() in user_tags
                }
            )

        data["tags"] = list(update_tags)

    if (alias := call.data.get(ATTR_ALIAS)) is not None:
        data["alias"] = alias

    if (cost := call.data.get(ATTR_COST)) is not None:
        data["value"] = cost

    if priority := call.data.get(ATTR_PRIORITY):
        data["priority"] = TaskPriority[priority]

    if frequency := call.data.get(ATTR_FREQUENCY):
        data["frequency"] = frequency
    else:
        frequency = current_task.frequency if current_task else Frequency.WEEKLY

    if up_down := call.data.get(ATTR_UP_DOWN):
        data["up"] = "up" in up_down
        data["down"] = "down" in up_down

    if counter_up := call.data.get(ATTR_COUNTER_UP):
        data["counterUp"] = counter_up

    if counter_down := call.data.get(ATTR_COUNTER_DOWN):
        data["counterDown"] = counter_down

    if due_date := call.data.get(ATTR_DATE):
        data["date"] = datetime.combine(due_date, time())

    if call.data.get(ATTR_CLEAR_DATE):
        data["date"] = None

    checklist = current_task.checklist if current_task else []

    if add_checklist_item := call.data.get(ATTR_ADD_CHECKLIST_ITEM):
        checklist.extend(
            Checklist(completed=False, id=uuid4(), text=item)
            for item in add_checklist_item
            if not any(i.text == item for i in checklist)
        )
    if remove_checklist_item := call.data.get(ATTR_REMOVE_CHECKLIST_ITEM):
        checklist = [
            item for item in checklist if item.text not in remove_checklist_item
        ]

    if score_checklist_item := call.data.get(ATTR_SCORE_CHECKLIST_ITEM):
        for item in checklist:
            if item.text in score_checklist_item:
                item.completed = True

    if unscore_checklist_item := call.data.get(ATTR_UNSCORE_CHECKLIST_ITEM):
        for item in checklist:
            if item.text in unscore_checklist_item:
                item.completed = False
    if (
        add_checklist_item
        or remove_checklist_item
        or score_checklist_item
        or unscore_checklist_item
    ):
        data["checklist"] = checklist

    if collapse_checklist := call.data.get(ATTR_COLLAPSE_CHECKLIST):
        data["collapseChecklist"] = COLLAPSE_CHECKLIST_MAP[collapse_checklist]

    reminders = current_task.reminders if current_task else []

    if add_reminders := call.data.get(ATTR_REMINDER):
        if task_type is TaskType.TODO:
            existing_reminder_datetimes = {
                r.time.replace(tzinfo=None) for r in reminders
            }

            reminders.extend(
                Reminders(id=uuid4(), time=r)
                for r in add_reminders
                if r not in existing_reminder_datetimes
            )
        if task_type is TaskType.DAILY:
            existing_reminder_times = {
                r.time.time().replace(microsecond=0, second=0) for r in reminders
            }

            reminders.extend(
                Reminders(
                    id=uuid4(),
                    time=datetime.combine(date.today(), r, tzinfo=UTC),
                )
                for r in add_reminders
                if r not in existing_reminder_times
            )

    if remove_reminder := call.data.get(ATTR_REMOVE_REMINDER):
        if task_type is TaskType.TODO:
            reminders = list(
                filter(
                    lambda r: r.time.replace(tzinfo=None) not in remove_reminder,
                    reminders,
                )
            )
        if task_type is TaskType.DAILY:
            reminders = list(
                filter(
                    lambda r: (
                        r.time.time().replace(second=0, microsecond=0)
                        not in remove_reminder
                    ),
                    reminders,
                )
            )

    if clear_reminders := call.data.get(ATTR_CLEAR_REMINDER):
        reminders = []

    if add_reminders or remove_reminder or clear_reminders:
        data["reminders"] = reminders

    if start_date := call.data.get(ATTR_START_DATE):
        data["startDate"] = datetime.combine(start_date, time())
    else:
        start_date = (
            current_task.startDate
            if current_task and current_task.startDate
            else dt_util.start_of_local_day()
        )
    if repeat := call.data.get(ATTR_REPEAT):
        if frequency is Frequency.WEEKLY:
            data["repeat"] = Repeat(**{d: d in repeat for d in WEEK_DAYS})
        else:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="frequency_not_weekly",
            )
    if repeat_monthly := call.data.get(ATTR_REPEAT_MONTHLY):
        if frequency is not Frequency.MONTHLY:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="frequency_not_monthly",
            )

        if repeat_monthly == "day_of_week":
            weekday = start_date.weekday()
            data["weeksOfMonth"] = [(start_date.day - 1) // 7]
            data["repeat"] = Repeat(
                **{day: i == weekday for i, day in enumerate(WEEK_DAYS)}
            )
            data["daysOfMonth"] = []

        else:
            data["daysOfMonth"] = [start_date.day]
            data["weeksOfMonth"] = []

    if interval := call.data.get(ATTR_INTERVAL):
        data["everyX"] = interval

    if streak := call.data.get(ATTR_STREAK):
        data["streak"] = streak

    try:
        if is_update:
            if TYPE_CHECKING:
                assert current_task
                assert current_task.id
            response = await coordinator.habitica.update_task(current_task.id, data)
        else:
            response = await coordinator.habitica.create_task(data)
    except TooManyRequestsError as e:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="setup_rate_limit_exception",
            translation_placeholders={"retry_after": str(e.retry_after)},
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
        return response.data.to_dict(omit_none=True)