def run_api(
    host: str = '0.0.0.0',
    port: int = None,
    bind: str = None,
    debug: bool = False,
    use_colors: bool = None,
    **kwargs
) -> None:
    print(f'Starting server... [g4f v-{g4f.version.utils.current_version}]' + (" (debug)" if debug else ""))

    if use_colors is None:
        use_colors = debug

    if bind is not None:
        host, port = bind.split(":")

    if port is None:
        port = DEFAULT_PORT

    if AppConfig.demo and debug:
        method = "create_app_with_demo_and_debug"
    elif AppConfig.gui and debug:
        method = "create_app_with_gui_and_debug"
    else:
        method = "create_app_debug" if debug else "create_app"

    uvicorn.run(
        f"g4f.api:{method}",
        host=host,
        port=int(port),
        factory=True,
        use_colors=use_colors,
        **filter_none(**kwargs)
    )