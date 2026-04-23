def validate_iqs_file(config: Config, integration: Integration) -> None:
    """Validate quality scale file for integration."""
    if not integration.core:
        return

    declared_quality_scale = QUALITY_SCALE_TIERS.get(integration.quality_scale)

    iqs_file = integration.path / "quality_scale.yaml"
    has_file = iqs_file.is_file()
    if not has_file:
        if (
            integration.domain not in INTEGRATIONS_WITHOUT_QUALITY_SCALE_FILE
            and integration.domain not in NO_QUALITY_SCALE
            and integration.integration_type != IntegrationType.VIRTUAL
        ):
            integration.add_error(
                "quality_scale",
                (
                    "New integrations marked as internal should be added to NO_QUALITY_SCALE in script/hassfest/quality_scale.py."
                    if integration.quality_scale == "internal"
                    else "Quality scale definition not found. New integrations are required to at least reach the Bronze tier."
                ),
            )
            return
        if declared_quality_scale is not None:
            integration.add_error(
                "quality_scale",
                "Quality scale definition not found. Integrations that set a manifest quality scale must have a quality scale definition.",
            )
            return
        return
    if integration.integration_type == IntegrationType.VIRTUAL:
        integration.add_error(
            "quality_scale",
            "Virtual integrations are not allowed to have a quality scale file.",
        )
        return
    if integration.domain in NO_QUALITY_SCALE:
        integration.add_error(
            "quality_scale",
            "This integration is not supposed to have a quality scale file.",
        )
        return
    if integration.domain in INTEGRATIONS_WITHOUT_QUALITY_SCALE_FILE:
        integration.add_error(
            "quality_scale",
            "Quality scale file found! Please remove from `INTEGRATIONS_WITHOUT_QUALITY_SCALE_FILE`"
            " in script/hassfest/quality_scale.py",
        )
        return
    if (
        integration.domain in INTEGRATIONS_WITHOUT_SCALE
        and declared_quality_scale is not None
    ):
        integration.add_error(
            "quality_scale",
            "This integration is graded and should be removed from `INTEGRATIONS_WITHOUT_SCALE`"
            " in script/hassfest/quality_scale.py",
        )
        return
    if (
        integration.domain not in INTEGRATIONS_WITHOUT_SCALE
        and declared_quality_scale is None
    ):
        integration.add_error(
            "quality_scale",
            (
                "New integrations marked as internal should be added to INTEGRATIONS_WITHOUT_SCALE in script/hassfest/quality_scale.py."
                if integration.quality_scale == "internal"
                else "New integrations are required to at least reach the Bronze tier."
            ),
        )
        return
    name = str(iqs_file)

    try:
        data = load_yaml_dict(name)
    except HomeAssistantError:
        integration.add_error("quality_scale", "Invalid quality_scale.yaml")
        return

    try:
        SCHEMA(data)
    except vol.Invalid as err:
        integration.add_error(
            "quality_scale", f"Invalid {name}: {humanize_error(data, err)}"
        )

    rules_done = set[str]()
    rules_met = set[str]()
    for rule_name, rule_value in data.get("rules", {}).items():
        status = rule_value["status"] if isinstance(rule_value, dict) else rule_value
        if status not in {"done", "exempt"}:
            continue
        rules_met.add(rule_name)
        if status == "done":
            rules_done.add(rule_name)

    for rule_name in rules_done:
        if (validator := VALIDATORS.get(rule_name)) and (
            errors := validator.validate(config, integration, rules_done=rules_done)
        ):
            for error in errors:
                integration.add_error("quality_scale", f"[{rule_name}] {error}")
            integration.add_error("quality_scale", RULE_URL.format(rule_name=rule_name))

    # An integration must have all the necessary rules for the declared
    # quality scale, and all the rules below.
    if declared_quality_scale is None:
        return

    for scale in ScaledQualityScaleTiers:
        if scale > declared_quality_scale:
            break
        required_rules = set(SCALE_RULES[scale])
        if missing_rules := (required_rules - rules_met):
            friendly_rule_str = "\n".join(
                f"  {rule}: todo" for rule in sorted(missing_rules)
            )
            integration.add_error(
                "quality_scale",
                f"Quality scale tier {scale.name.lower()} requires quality scale rules to be met:\n{friendly_rule_str}",
            )