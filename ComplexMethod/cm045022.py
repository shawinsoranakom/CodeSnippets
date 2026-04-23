def validate_workflow(definition: WorkflowDefinition) -> list[str]:
    """Validate a workflow definition and return a list of error messages.

    An empty list means the workflow is valid.
    """
    errors: list[str] = []

    # -- Schema version ---------------------------------------------------
    if definition.schema_version not in ("1.0", "1"):
        errors.append(
            f"Unsupported schema_version {definition.schema_version!r}. "
            f"Expected '1.0'."
        )

    # -- Top-level fields -------------------------------------------------
    if not definition.id:
        errors.append("Workflow is missing 'workflow.id'.")
    elif not _ID_PATTERN.match(definition.id):
        errors.append(
            f"Workflow ID {definition.id!r} must be lowercase alphanumeric "
            f"with hyphens."
        )

    if not definition.name:
        errors.append("Workflow is missing 'workflow.name'.")

    if not definition.version:
        errors.append("Workflow is missing 'workflow.version'.")
    elif not re.match(r"^\d+\.\d+\.\d+$", definition.version):
        errors.append(
            f"Workflow version {definition.version!r} is not valid "
            f"semantic versioning (expected X.Y.Z)."
        )

    # -- Inputs -----------------------------------------------------------
    if not isinstance(definition.inputs, dict):
        errors.append("'inputs' must be a mapping (or omitted).")
    else:
        for input_name, input_def in definition.inputs.items():
            if not isinstance(input_def, dict):
                errors.append(f"Input {input_name!r} must be a mapping.")
                continue
            input_type = input_def.get("type")
            if input_type and input_type not in ("string", "number", "boolean"):
                errors.append(
                    f"Input {input_name!r} has invalid type {input_type!r}. "
                    f"Must be 'string', 'number', or 'boolean'."
                )

    # -- Steps ------------------------------------------------------------
    if not isinstance(definition.steps, list):
        errors.append("'steps' must be a list.")
        return errors
    if not definition.steps:
        errors.append("Workflow has no steps defined.")

    seen_ids: set[str] = set()
    _validate_steps(definition.steps, seen_ids, errors)

    return errors