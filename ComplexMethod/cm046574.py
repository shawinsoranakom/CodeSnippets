def _collect_validation_errors(recipe: dict[str, Any]) -> list[ValidateError]:
    try:
        from data_designer.engine.compiler import (
            _add_internal_row_id_column_if_needed,
            _get_allowed_references,
            _resolve_and_add_seed_columns,
        )
        from data_designer.engine.validation import (
            ViolationLevel,
            validate_data_designer_config,
        )
    except ImportError:
        return []

    try:
        builder = build_config_builder(recipe)
        designer = create_data_designer(recipe)
        resource_provider = designer._create_resource_provider(  # type: ignore[attr-defined]
            "validate-configuration",
            builder,
        )
        config = builder.build()
        _resolve_and_add_seed_columns(config, resource_provider.seed_reader)
        _add_internal_row_id_column_if_needed(config)
        violations = validate_data_designer_config(
            columns = config.columns,
            processor_configs = config.processors or [],
            allowed_references = _get_allowed_references(config),
        )
    except (TypeError, ValueError, AttributeError):
        return []

    errors: list[ValidateError] = []
    for violation in violations:
        if violation.level != ViolationLevel.ERROR:
            continue
        code = getattr(violation.type, "value", None)
        path = violation.column if violation.column else None
        message = str(violation.message).strip() or "Validation failed."
        errors.append(
            ValidateError(
                message = message,
                path = path,
                code = code,
            )
        )
    return errors