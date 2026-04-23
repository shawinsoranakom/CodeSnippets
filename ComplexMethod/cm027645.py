def _find_referenced_target(
        target: Literal["area_id", "floor_id", "label_id"],
        referenced: set[str],
        sequence: Sequence[dict[str, Any]],
    ) -> None:
        """Find referenced target in a sequence."""
        for step in sequence:
            action = cv.determine_script_action(step)

            if action == cv.SCRIPT_ACTION_CALL_SERVICE:
                for data in (
                    step.get(CONF_TARGET),
                    step.get(CONF_SERVICE_DATA),
                    step.get(CONF_SERVICE_DATA_TEMPLATE),
                ):
                    _referenced_extract_ids(data, target, referenced)

            elif action == cv.SCRIPT_ACTION_CHECK_CONDITION:
                referenced |= condition.async_extract_targets(step, target)

            elif action == cv.SCRIPT_ACTION_WAIT_FOR_TRIGGER:
                for trigger in step[CONF_WAIT_FOR_TRIGGER]:
                    referenced |= set(
                        trigger_helper.async_extract_targets(trigger, target)
                    )

            elif action == cv.SCRIPT_ACTION_CHOOSE:
                for choice in step[CONF_CHOOSE]:
                    for cond in choice[CONF_CONDITIONS]:
                        referenced |= condition.async_extract_targets(cond, target)
                    Script._find_referenced_target(
                        target, referenced, choice[CONF_SEQUENCE]
                    )
                if CONF_DEFAULT in step:
                    Script._find_referenced_target(
                        target, referenced, step[CONF_DEFAULT]
                    )

            elif action == cv.SCRIPT_ACTION_IF:
                for cond in step[CONF_IF]:
                    referenced |= condition.async_extract_targets(cond, target)
                Script._find_referenced_target(target, referenced, step[CONF_THEN])
                if CONF_ELSE in step:
                    Script._find_referenced_target(target, referenced, step[CONF_ELSE])

            elif action == cv.SCRIPT_ACTION_PARALLEL:
                for script in step[CONF_PARALLEL]:
                    Script._find_referenced_target(
                        target, referenced, script[CONF_SEQUENCE]
                    )

            elif action == cv.SCRIPT_ACTION_SEQUENCE:
                Script._find_referenced_target(target, referenced, step[CONF_SEQUENCE])