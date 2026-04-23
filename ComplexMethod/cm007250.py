async def _load_components_dynamically(
    target_modules: list[str] | None = None,
) -> dict[str, Any]:
    """Load components dynamically by scanning and importing modules.

    Args:
        target_modules: Optional list of specific module names to load (e.g., ["mistral", "openai"])

    Returns:
        Dictionary mapping top-level module names to their components
    """
    modules_dict: dict[str, Any] = {}

    try:
        import lfx.components as components_pkg
    except ImportError as e:
        await logger.aerror(f"Failed to import langflow.components package: {e}", exc_info=True)
        return modules_dict

    # Collect all module names to process
    module_names = []
    for _, modname, _ in pkgutil.walk_packages(components_pkg.__path__, prefix=components_pkg.__name__ + "."):
        # Skip if the module is in the deactivated folder
        if "deactivated" in modname:
            continue

        # Parse module name once for all checks
        parts = modname.split(".")
        if len(parts) > MIN_MODULE_PARTS:
            component_type = parts[2]

            # Skip disabled components when ASTRA_CLOUD_DISABLE_COMPONENT is true
            if len(parts) >= MIN_MODULE_PARTS_WITH_FILENAME:
                module_filename = parts[3]
                if is_component_disabled_in_astra_cloud(component_type.lower(), module_filename):
                    continue

            # If specific modules requested, filter by top-level module name
            if target_modules and component_type.lower() not in target_modules:
                continue

        module_names.append(modname)

    if target_modules:
        await logger.adebug(f"Found {len(module_names)} modules matching filter")

    if not module_names:
        return modules_dict

    # Create tasks for parallel module processing
    tasks = [asyncio.to_thread(_process_single_module, modname) for modname in module_names]

    # Wait for all modules to be processed
    try:
        module_results = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:  # noqa: BLE001
        await logger.aerror(f"Error during parallel module processing: {e}", exc_info=True)
        return modules_dict

    # Merge results from all modules
    for result in module_results:
        if isinstance(result, Exception):
            await logger.awarning(f"Module processing failed: {result}")
            continue

        if result and isinstance(result, tuple) and len(result) == EXPECTED_RESULT_LENGTH:
            top_level, components = result
            if top_level and components:
                if top_level not in modules_dict:
                    modules_dict[top_level] = {}
                modules_dict[top_level].update(components)

    return modules_dict