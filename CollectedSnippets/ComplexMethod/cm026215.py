async def handle_new_task(call: ServiceCall) -> None:
        """Call when a user creates a new Todoist Task from Home Assistant."""
        project_name = call.data[PROJECT_NAME]
        projects = await coordinator.async_get_projects()
        project_id: str | None = None
        for project in projects:
            if project_name == project.name.lower():
                project_id = project.id
                break
        if project_id is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="project_invalid",
                translation_placeholders={
                    "project": project_name,
                },
            )

        # Optional section within project
        section_id: str | None = None
        if SECTION_NAME in call.data:
            section_name = call.data[SECTION_NAME]
            sections = await coordinator.async_get_sections(project_id)
            for section in sections:
                if section_name == section.name.lower():
                    section_id = section.id
                    break
            if section_id is None:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="section_invalid",
                    translation_placeholders={
                        "section": section_name,
                        "project": project_name,
                    },
                )

        # Create the task
        content = call.data[CONTENT]
        data: dict[str, Any] = {"project_id": project_id}

        if description := call.data.get(DESCRIPTION):
            data["description"] = description

        if section_id is not None:
            data["section_id"] = section_id

        if task_labels := call.data.get(LABELS):
            data["labels"] = task_labels

        if ASSIGNEE in call.data:
            collaborators_result = await coordinator.api.get_collaborators(project_id)
            all_collaborators = await flatten_async_pages(collaborators_result)
            collaborator_id_lookup = {
                collab.name.lower(): collab.id for collab in all_collaborators
            }
            task_assignee = call.data[ASSIGNEE].lower()
            if task_assignee in collaborator_id_lookup:
                data["assignee_id"] = collaborator_id_lookup[task_assignee]
            else:
                raise ValueError(
                    f"User is not part of the shared project. user: {task_assignee}"
                )

        if PRIORITY in call.data:
            data["priority"] = call.data[PRIORITY]

        if DUE_DATE_STRING in call.data:
            data["due_string"] = call.data[DUE_DATE_STRING]

        if DUE_DATE_LANG in call.data:
            data["due_lang"] = call.data[DUE_DATE_LANG]

        if DUE_DATE in call.data:
            due_date = dt_util.parse_datetime(call.data[DUE_DATE])
            if due_date is None:
                due = dt_util.parse_date(call.data[DUE_DATE])
                if due is None:
                    raise ValueError(f"Invalid due_date: {call.data[DUE_DATE]}")
                due_date = datetime(due.year, due.month, due.day)
            # Pass the datetime object directly - the library handles formatting
            data["due_datetime"] = dt_util.as_utc(due_date)

        api_task = await coordinator.api.add_task(content, **data)

        # The REST API doesn't support reminders, so we use the Sync API directly
        # to maintain functional parity with the component.
        # https://developer.todoist.com/api/v1/#tag/Sync/Reminders/Add-a-reminder
        _reminder_due: dict = {}
        if REMINDER_DATE_STRING in call.data:
            _reminder_due["string"] = call.data[REMINDER_DATE_STRING]

        if REMINDER_DATE_LANG in call.data:
            _reminder_due["lang"] = call.data[REMINDER_DATE_LANG]

        if REMINDER_DATE in call.data:
            reminder_date = dt_util.parse_datetime(call.data[REMINDER_DATE])
            if reminder_date is None:
                reminder = dt_util.parse_date(call.data[REMINDER_DATE])
                if reminder is None:
                    raise ValueError(
                        f"Invalid reminder_date: {call.data[REMINDER_DATE]}"
                    )
                reminder_date = datetime(reminder.year, reminder.month, reminder.day)
            # Format it in the manner Todoist expects (UTC with Z suffix)
            reminder_date = dt_util.as_utc(reminder_date)
            date_format = "%Y-%m-%dT%H:%M:%S.000000Z"
            _reminder_due["date"] = datetime.strftime(reminder_date, date_format)

        if _reminder_due:
            sync_url = "https://api.todoist.com/api/v1/sync"
            reminder_data = {
                "commands": [
                    {
                        "type": "reminder_add",
                        "temp_id": str(uuid.uuid1()),
                        "uuid": str(uuid.uuid1()),
                        "args": {
                            "item_id": api_task.id,
                            "type": "absolute",
                            "due": _reminder_due,
                        },
                    }
                ]
            }
            headers = {
                "Authorization": f"Bearer {coordinator.token}",
                "Content-Type": "application/json",
            }
            await session.post(sync_url, headers=headers, json=reminder_data)

        _LOGGER.debug("Created Todoist task: %s", call.data[CONTENT])