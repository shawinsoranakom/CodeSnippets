def __getattr__(attr_name: str) -> Any:
    """Lazily import component modules or individual components on attribute access.

    Supports both:
    - components.agents (module access)
    - components.AgentComponent (direct component access)

    Uses on-demand discovery - only scans modules when components are requested.
    """
    # First check if we already know about this attribute
    if attr_name not in _dynamic_imports:
        # Try to discover components from modules that might have this component
        # Get all module names we haven't discovered yet
        undiscovered_modules = [
            name
            for name in _dynamic_imports
            if _dynamic_imports[name] == "__module__" and name not in _discovered_modules and name != "Notion"
        ]

        # Discover components from undiscovered modules
        # Try all undiscovered modules until we find the component or exhaust the list
        for module_name in undiscovered_modules:
            _discover_components_from_module(module_name)
            # Check if we found what we're looking for
            if attr_name in _dynamic_imports:
                break

    # If still not found, raise AttributeError
    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)

    try:
        module_path = _dynamic_imports[attr_name]

        if module_path == "__module__":
            # This is a module import (e.g., components.agents)
            result = import_mod(attr_name, "__module__", __spec__.parent)
            # After importing a module, discover its components
            _discover_components_from_module(attr_name)
        elif "." in module_path:
            # This is a component import (e.g., components.AgentComponent -> agents.agent)
            module_name, component_file = module_path.split(".", 1)
            # Check if this is an alias module (data, helpers, logic, models)
            # These modules forward to other modules, so we need to import directly from the module
            # instead of trying to import from a submodule that doesn't exist
            if module_name in ("data", "helpers", "logic", "models"):
                # For alias modules, import the module and get the component directly
                alias_module = import_mod(module_name, "__module__", __spec__.parent)
                result = getattr(alias_module, attr_name)
            else:
                # Import the specific component from its module
                result = import_mod(attr_name, component_file, f"{__spec__.parent}.{module_name}")
        else:
            # Fallback to regular import
            result = import_mod(attr_name, module_path, __spec__.parent)

    except (ImportError, AttributeError) as e:
        # Check if this is a missing dependency issue by looking at the error message
        if "No module named" in str(e):
            # Extract the missing module name and suggest installation
            import re

            match = re.search(r"No module named '([^']+)'", str(e))
            if match:
                missing_module = match.group(1)
                msg = f"Could not import '{attr_name}' from '{__name__}'. Missing dependency: '{missing_module}'. "
            else:
                msg = f"Could not import '{attr_name}' from '{__name__}'. Missing dependencies: {e}"
        elif "cannot import name" in str(e):
            msg = f"Could not import '{attr_name}' from '{__name__}'. Import error: {e}"
        else:
            msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e

    globals()[attr_name] = result
    return result