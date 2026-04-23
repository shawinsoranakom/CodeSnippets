def load_local_registry() -> dict[str, dict]:
    """Load the component registry from the bundled index file.

    Returns a flat dict: {component_type: template_dict}.
    Results are cached after the first call.

    Raises:
        RuntimeError: If the index file is missing, corrupt, or empty.
    """
    global _registry_cache  # noqa: PLW0603
    if _registry_cache is not None:
        return _registry_cache

    try:
        with _INDEX_PATH.open() as f:
            data = json.load(f)
    except FileNotFoundError:
        msg = f"Component registry not found at {_INDEX_PATH}. The lfx package may be installed incorrectly."
        raise RuntimeError(msg) from None
    except (json.JSONDecodeError, OSError) as e:
        msg = f"Failed to load component registry from {_INDEX_PATH}: {e}"
        raise RuntimeError(msg) from e

    registry: dict[str, dict] = {}
    for cat in data.get("entries", []):
        if isinstance(cat, list) and len(cat) > 1 and isinstance(cat[1], dict):
            category_name = cat[0] if isinstance(cat[0], str) else ""
            for name, comp_data in cat[1].items():
                if isinstance(comp_data, dict) and "template" in comp_data:
                    registry[name] = {**comp_data, "category": category_name}

    if not registry:
        msg = f"Component registry at {_INDEX_PATH} contains no valid components."
        raise RuntimeError(msg)

    logger.debug("Loaded %d components from local registry", len(registry))
    _registry_cache = registry
    return registry