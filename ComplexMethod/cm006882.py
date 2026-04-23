async def aload_flow_from_json(
    flow: Path | str | dict,
    *,
    tweaks: dict | None = None,
    log_level: str | None = None,
    log_file: str | None = None,
    log_rotation: str | None = None,
    env_file: str | None = None,
    cache: str | None = None,
    disable_logs: bool | None = True,
) -> "Graph":
    """Load a flow graph from a JSON file or a JSON object.

    Args:
        flow (Union[Path, str, dict]): The flow to load. It can be a file path (str or Path object)
            or a JSON object (dict).
        tweaks (Optional[dict]): Optional tweaks to apply to the loaded flow graph.
        log_level (Optional[str]): Optional log level to configure for the flow processing.
        log_file (Optional[str]): Optional log file to configure for the flow processing.
        log_rotation (Optional[str]): Optional log rotation(Time/Size) to configure for the flow processing.
        env_file (Optional[str]): Optional .env file to override environment variables.
        cache (Optional[str]): Optional cache path to update the flow settings.
        disable_logs (Optional[bool], default=True): Optional flag to disable logs during flow processing.
            If log_level or log_file are set, disable_logs is not used.

    Returns:
        Graph: The loaded flow graph as a Graph object.

    Raises:
        TypeError: If the input is neither a file path (str or Path object) nor a JSON object (dict).

    """
    # If input is a file path, load JSON from the file
    log_file_path = Path(log_file) if log_file else None
    configure(log_level=log_level, log_file=log_file_path, disable=disable_logs, log_rotation=log_rotation)

    # override env variables with .env file
    if env_file and tweaks is not None:
        async with aiofiles.open(Path(env_file), encoding="utf-8") as f:
            content = await f.read()
            env_vars = dotenv_values(stream=StringIO(content))
        tweaks = replace_tweaks_with_env(tweaks=tweaks, env_vars=env_vars)

    # Update settings with cache and components path
    await update_settings(cache=cache)

    if isinstance(flow, str | Path):
        async with aiofiles.open(Path(flow), encoding="utf-8") as f:
            content = await f.read()
            flow_graph = json.loads(content)
    # If input is a dictionary, assume it's a JSON object
    elif isinstance(flow, dict):
        flow_graph = flow
    else:
        msg = "Input must be either a file path (str) or a JSON object (dict)"
        raise TypeError(msg)

    graph_data = flow_graph["data"]
    if tweaks is not None:
        graph_data = process_tweaks(graph_data, tweaks)

    try:
        await ensure_component_hash_lookups_loaded()
    except CustomComponentValidationError:
        raise
    except Exception as exc:
        msg = (
            "Failed to load component templates for validation. "
            "Ensure the server is fully initialized before loading flows."
        )
        raise CustomComponentValidationError(msg) from exc

    from lfx.graph.graph.base import Graph

    return Graph.from_payload(graph_data)