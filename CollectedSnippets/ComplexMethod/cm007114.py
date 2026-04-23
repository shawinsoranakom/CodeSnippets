def __getattr__(attr_name: str) -> Any:
    """Lazily import helper components on attribute access."""
    # Handle submodule access for backwards compatibility
    # e.g., lfx.components.helpers.id_generator -> lfx.components.utilities.id_generator
    if attr_name == "id_generator":
        from importlib import import_module

        result = import_module("lfx.components.utilities.id_generator")
        globals()[attr_name] = result
        return result
    if attr_name == "calculator_core":
        from importlib import import_module

        result = import_module("lfx.components.utilities.calculator_core")
        globals()[attr_name] = result
        return result
    if attr_name == "current_date":
        from importlib import import_module

        result = import_module("lfx.components.utilities.current_date")
        globals()[attr_name] = result
        return result
    if attr_name == "memory":
        from importlib import import_module

        result = import_module("lfx.components.models_and_agents.memory")
        globals()[attr_name] = result
        return result

    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)

    # CurrentDateComponent, CalculatorComponent, and IDGeneratorComponent were moved to utilities
    # Forward them to utilities for backwards compatibility
    if attr_name in ("CurrentDateComponent", "CalculatorComponent", "IDGeneratorComponent"):
        from lfx.components import utilities

        result = getattr(utilities, attr_name)
        globals()[attr_name] = result
        return result

    # MemoryComponent was moved to models_and_agents
    # Forward it to models_and_agents for backwards compatibility
    if attr_name == "MemoryComponent":
        from lfx.components import models_and_agents

        result = getattr(models_and_agents, attr_name)
        globals()[attr_name] = result
        return result

    # CreateListComponent, MessageStoreComponent, and OutputParserComponent were moved to processing
    # Forward them to processing for backwards compatibility
    if attr_name == "CreateListComponent":
        from lfx.components import processing

        result = getattr(processing, attr_name)
        globals()[attr_name] = result
        return result
    if attr_name == "MessageStoreComponent":
        from lfx.components import processing

        result = processing.MessageStoreComponent
        globals()[attr_name] = result
        return result
    if attr_name == "OutputParserComponent":
        from lfx.components import processing

        result = getattr(processing, attr_name)
        globals()[attr_name] = result
        return result

    try:
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    globals()[attr_name] = result
    return result