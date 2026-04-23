def _validate_steps(
    steps: list[dict[str, Any]],
    seen_ids: set[str],
    errors: list[str],
) -> None:
    """Recursively validate a list of steps."""
    from . import STEP_REGISTRY

    for step_config in steps:
        if not isinstance(step_config, dict):
            errors.append(f"Step must be a mapping, got {type(step_config).__name__}.")
            continue

        step_id = step_config.get("id")
        if not step_id:
            errors.append("Step is missing 'id' field.")
            continue

        if ":" in step_id:
            errors.append(
                f"Step ID {step_id!r} contains ':' which is reserved "
                f"for engine-generated nested IDs (parentId:childId)."
            )

        if step_id in seen_ids:
            errors.append(f"Duplicate step ID {step_id!r}.")
        seen_ids.add(step_id)

        # Determine step type
        step_type = step_config.get("type", "command")
        if step_type not in _get_valid_step_types():
            errors.append(
                f"Step {step_id!r} has invalid type {step_type!r}."
            )
            continue

        # Delegate to step-specific validation
        step_impl = STEP_REGISTRY.get(step_type)
        if step_impl:
            step_errors = step_impl.validate(step_config)
            errors.extend(step_errors)

        # Recursively validate nested steps
        for nested_key in ("then", "else", "steps"):
            nested = step_config.get(nested_key)
            if isinstance(nested, list):
                _validate_steps(nested, seen_ids, errors)

        # Validate switch cases
        cases = step_config.get("cases")
        if isinstance(cases, dict):
            for _case_key, case_steps in cases.items():
                if isinstance(case_steps, list):
                    _validate_steps(case_steps, seen_ids, errors)

        # Validate switch default
        default = step_config.get("default")
        if isinstance(default, list):
            _validate_steps(default, seen_ids, errors)

        # Validate fan-out nested step (template — not added to seen_ids
        # since the engine generates parentId:templateId:index at runtime)
        fan_step = step_config.get("step")
        if isinstance(fan_step, dict):
            fan_errors: list[str] = []
            _validate_steps([fan_step], set(), fan_errors)
            errors.extend(fan_errors)