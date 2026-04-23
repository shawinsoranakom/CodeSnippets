def _validate_integration(config: Config, integration: Integration) -> None:
    """Validate integration has has a configuration schema."""
    if integration.domain in CONFIG_SCHEMA_IGNORE:
        return

    init_file = integration.path / "__init__.py"

    if not init_file.is_file():
        # Virtual integrations don't have any implementation
        return

    init = ast_parse_module(init_file)

    # No YAML Support
    if not _has_function(
        init, ast.AsyncFunctionDef, "async_setup"
    ) and not _has_function(init, ast.FunctionDef, "setup"):
        return

    # No schema
    if (
        _has_assignment(init, "CONFIG_SCHEMA")
        or _has_assignment(init, "PLATFORM_SCHEMA")
        or _has_assignment(init, "PLATFORM_SCHEMA_BASE")
        or _has_import(init, "CONFIG_SCHEMA")
        or _has_import(init, "PLATFORM_SCHEMA")
        or _has_import(init, "PLATFORM_SCHEMA_BASE")
    ):
        return

    config_file = integration.path / "config.py"
    if config_file.is_file():
        config_module = ast_parse_module(config_file)
        if _has_function(config_module, ast.AsyncFunctionDef, "async_validate_config"):
            return

    if config.specific_integrations:
        notice_method = integration.add_warning
    else:
        notice_method = integration.add_error

    notice_method(
        "config_schema",
        "Integrations which implement 'async_setup' or 'setup' must define either "
        "'CONFIG_SCHEMA', 'PLATFORM_SCHEMA' or 'PLATFORM_SCHEMA_BASE'. If the "
        "integration has no configuration parameters, can only be set up from platforms"
        " or can only be set up from config entries, one of the helpers "
        "cv.empty_config_schema, cv.platform_only_config_schema or "
        "cv.config_entry_only_config_schema can be used.",
    )