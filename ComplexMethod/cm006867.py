def validate_flow_file(
    path: Path,
    *,
    level: int = LEVEL_REQUIRED_INPUTS,
    skip_components: bool = False,
    skip_edge_types: bool = False,
    skip_required_inputs: bool = False,
    skip_version_check: bool = False,
    skip_credentials: bool = False,
) -> ValidationResult:
    result = ValidationResult(path=path)

    try:
        raw = path.read_text(encoding="utf-8")
        flow: dict[str, Any] = json.loads(raw)
    except OSError as exc:
        result.issues.append(
            ValidationIssue(
                level=LEVEL_STRUCTURAL,
                severity="error",
                node_id=None,
                node_name=None,
                message=f"Cannot read file: {exc}",
            )
        )
        return result
    except json.JSONDecodeError as exc:
        result.issues.append(
            ValidationIssue(
                level=LEVEL_STRUCTURAL,
                severity="error",
                node_id=None,
                node_name=None,
                message=f"Invalid JSON: {exc}",
            )
        )
        return result

    # Level 1 - structural (JSON shape + orphaned/unused node checks)
    can_continue = _check_structural(flow, result)
    if can_continue:
        _check_orphaned_nodes(flow, result)
        _check_unused_nodes(flow, result)
        # Extended: version mismatch / outdated components
        if not skip_version_check:
            _check_version_mismatch(flow, result)
    if not can_continue or level < LEVEL_COMPONENTS:
        return result

    # Level 2 - component existence
    if not skip_components:
        _check_component_existence(flow, result)
    if level < LEVEL_EDGE_TYPES:
        return result

    # Level 3 - edge type compatibility
    if not skip_edge_types:
        _check_edge_type_compatibility(flow, result)
    if level < LEVEL_REQUIRED_INPUTS:
        return result

    # Level 4 - required inputs + extended: missing credentials
    if not skip_required_inputs:
        _check_required_inputs(flow, result)
    if not skip_credentials:
        _check_missing_credentials(flow, result)

    return result