def __getattr__(attr_name: str) -> Any:
    """Lazily import logic components on attribute access."""
    # Handle submodule access for backwards compatibility
    if attr_name == "listen":
        from importlib import import_module

        result = import_module("lfx.components.flow_controls.listen")
        globals()[attr_name] = result
        return result
    if attr_name == "loop":
        from importlib import import_module

        result = import_module("lfx.components.flow_controls.loop")
        globals()[attr_name] = result
        return result
    if attr_name == "notify":
        from importlib import import_module

        result = import_module("lfx.components.flow_controls.notify")
        globals()[attr_name] = result
        return result
    if attr_name == "pass_message":
        from importlib import import_module

        result = import_module("lfx.components.flow_controls.pass_message")
        globals()[attr_name] = result
        return result
    if attr_name == "conditional_router":
        from importlib import import_module

        result = import_module("lfx.components.flow_controls.conditional_router")
        globals()[attr_name] = result
        return result
    if attr_name == "data_conditional_router":
        from importlib import import_module

        result = import_module("lfx.components.flow_controls.data_conditional_router")
        globals()[attr_name] = result
        return result
    if attr_name == "flow_tool":
        from importlib import import_module

        result = import_module("lfx.components.flow_controls.flow_tool")
        globals()[attr_name] = result
        return result
    if attr_name == "run_flow":
        from importlib import import_module

        result = import_module("lfx.components.flow_controls.run_flow")
        globals()[attr_name] = result
        return result
    if attr_name == "sub_flow":
        from importlib import import_module

        result = import_module("lfx.components.flow_controls.sub_flow")
        globals()[attr_name] = result
        return result

    if attr_name not in _dynamic_imports:
        msg = f"module '{__name__}' has no attribute '{attr_name}'"
        raise AttributeError(msg)

    # Most logic components were moved to flow_controls
    # Forward them to flow_controls for backwards compatibility
    if attr_name in (
        "ConditionalRouterComponent",
        "DataConditionalRouterComponent",
        "FlowToolComponent",
        "LoopComponent",
        "PassMessageComponent",
        "RunFlowComponent",
        "SubFlowComponent",
    ):
        from lfx.components import flow_controls

        result = getattr(flow_controls, attr_name)
        globals()[attr_name] = result
        return result

    # SmartRouterComponent was moved to llm_operations
    if attr_name == "SmartRouterComponent":
        from lfx.components import llm_operations

        result = getattr(llm_operations, attr_name)
        globals()[attr_name] = result
        return result

    try:
        result = import_mod(attr_name, _dynamic_imports[attr_name], __spec__.parent)
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        msg = f"Could not import '{attr_name}' from '{__name__}': {e}"
        raise AttributeError(msg) from e
    globals()[attr_name] = result
    return result