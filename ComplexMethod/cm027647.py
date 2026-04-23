def _find_referenced_entities(
        referenced: set[str], sequence: Sequence[dict[str, Any]]
    ) -> None:
        for step in sequence:
            action = cv.determine_script_action(step)

            if action == cv.SCRIPT_ACTION_CALL_SERVICE:
                for data in (
                    step,
                    step.get(CONF_TARGET),
                    step.get(CONF_SERVICE_DATA),
                    step.get(CONF_SERVICE_DATA_TEMPLATE),
                ):
                    _referenced_extract_ids(data, ATTR_ENTITY_ID, referenced)

            elif action == cv.SCRIPT_ACTION_CHECK_CONDITION:
                referenced |= condition.async_extract_entities(step)

            elif action == cv.SCRIPT_ACTION_WAIT_FOR_TRIGGER:
                for trigger in step[CONF_WAIT_FOR_TRIGGER]:
                    referenced |= set(trigger_helper.async_extract_entities(trigger))

            elif action == cv.SCRIPT_ACTION_ACTIVATE_SCENE:
                referenced.add(step[CONF_SCENE])

            elif action == cv.SCRIPT_ACTION_CHOOSE:
                for choice in step[CONF_CHOOSE]:
                    for cond in choice[CONF_CONDITIONS]:
                        referenced |= condition.async_extract_entities(cond)
                    Script._find_referenced_entities(referenced, choice[CONF_SEQUENCE])
                if CONF_DEFAULT in step:
                    Script._find_referenced_entities(referenced, step[CONF_DEFAULT])

            elif action == cv.SCRIPT_ACTION_IF:
                for cond in step[CONF_IF]:
                    referenced |= condition.async_extract_entities(cond)
                Script._find_referenced_entities(referenced, step[CONF_THEN])
                if CONF_ELSE in step:
                    Script._find_referenced_entities(referenced, step[CONF_ELSE])

            elif action == cv.SCRIPT_ACTION_PARALLEL:
                for script in step[CONF_PARALLEL]:
                    Script._find_referenced_entities(referenced, script[CONF_SEQUENCE])

            elif action == cv.SCRIPT_ACTION_SEQUENCE:
                Script._find_referenced_entities(referenced, step[CONF_SEQUENCE])