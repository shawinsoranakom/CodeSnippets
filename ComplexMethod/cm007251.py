def _process_single_module(modname: str) -> tuple[str, dict] | None:
    """Process a single module and return its components.

    Args:
        modname: The full module name to process

    Returns:
        A tuple of (top_level_package, components_dict) or None if processing failed
    """
    try:
        module = importlib.import_module(modname)
    except Exception as e:  # noqa: BLE001
        # Catch all exceptions during import to prevent component failures from crashing startup
        # TODO: Surface these errors to the UI in a friendly manner
        logger.error(f"Failed to import module {modname}: {e}", exc_info=True)
        return None
    # Extract the top-level subpackage name after "lfx.components."
    # e.g., "lfx.components.Notion.add_content_to_page" -> "Notion"
    mod_parts = modname.split(".")
    if len(mod_parts) <= MIN_MODULE_PARTS:
        return None

    top_level = mod_parts[2]
    module_components = {}

    # Bind frequently used functions for small speed gain
    _getattr = getattr

    # Fast path: only check class objects defined in this module
    failed_count = []
    for name, obj in vars(module).items():
        if not isinstance(obj, type):
            continue

        # Only consider classes defined in this module
        if obj.__module__ != modname:
            continue

        # Check for required attributes
        if not (
            _getattr(obj, "code_class_base_inheritance", None) is not None
            or _getattr(obj, "_code_class_base_inheritance", None) is not None
        ):
            continue

        try:
            comp_instance = obj()
            # modname is the full module name without the name of the obj
            full_module_name = f"{modname}.{name}"
            comp_template, _ = create_component_template(
                component_extractor=comp_instance, module_name=full_module_name
            )
            component_name = obj.name if hasattr(obj, "name") and obj.name else name
            module_components[component_name] = comp_template
        except Exception as e:  # noqa: BLE001
            failed_count.append(f"{name}: {e}")
            continue

    if failed_count:
        logger.warning(
            f"Skipped {len(failed_count)} component class{'es' if len(failed_count) != 1 else ''} "
            f"in module '{modname}' due to instantiation failure: {', '.join(failed_count)}"
        )
    logger.debug(f"Processed module {modname}")
    return (top_level, module_components)