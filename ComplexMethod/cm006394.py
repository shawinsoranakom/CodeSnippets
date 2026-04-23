async def _load_graph_from_python(
    flow_path: Path,
    provider: str | None = None,
    model_name: str | None = None,
    api_key_var: str | None = None,
) -> "Graph":
    """Load a Graph from a Python flow file.

    The Python file must define a function `get_graph()` that returns a Graph.
    The function can optionally accept provider, model_name, and api_key_var parameters.

    Args:
        flow_path: Path to the Python flow file.
        provider: Optional model provider (e.g., "OpenAI").
        model_name: Optional model name (e.g., "gpt-4o-mini").
        api_key_var: Optional API key variable name.

    Returns:
        Graph: The loaded and configured graph.

    Raises:
        HTTPException: If the flow file cannot be loaded or executed.
    """
    module_name = flow_path.stem
    spec = importlib.util.spec_from_file_location(module_name, flow_path)
    if spec is None or spec.loader is None:
        raise HTTPException(status_code=500, detail=f"Could not load flow module: {flow_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        with _temporary_sys_path(str(flow_path.parent)):
            spec.loader.exec_module(module)
    except Exception as e:
        if module_name in sys.modules:
            del sys.modules[module_name]
        logger.error(f"Error loading Python flow module: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading flow module: {e}") from e

    if not hasattr(module, "get_graph"):
        # Fallback: check for 'graph' variable for backward compatibility
        if hasattr(module, "graph"):
            graph = module.graph
            validate_flow_for_current_settings(graph)
            if module_name in sys.modules:
                del sys.modules[module_name]
            return graph
        if module_name in sys.modules:
            del sys.modules[module_name]
        raise HTTPException(status_code=500, detail=f"Flow module must define 'get_graph()' function: {flow_path}")

    get_graph_func = module.get_graph

    # Build kwargs for get_graph based on what it accepts
    sig = inspect.signature(get_graph_func)
    kwargs = {}
    if "provider" in sig.parameters and provider:
        kwargs["provider"] = provider
    if "model_name" in sig.parameters and model_name:
        kwargs["model_name"] = model_name
    if "api_key_var" in sig.parameters and api_key_var:
        kwargs["api_key_var"] = api_key_var

    try:
        if inspect.iscoroutinefunction(get_graph_func):
            graph = await get_graph_func(**kwargs)
        else:
            graph = get_graph_func(**kwargs)
    except Exception as e:
        logger.error(f"Error executing get_graph(): {e}")
        raise HTTPException(status_code=500, detail=f"Error creating graph: {e}") from e
    finally:
        if module_name in sys.modules:
            del sys.modules[module_name]

    validate_flow_for_current_settings(graph)
    return graph