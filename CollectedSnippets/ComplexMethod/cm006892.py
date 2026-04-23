def _resolve_remote_client(request: pytest.FixtureRequest) -> Any | None:
    """Return a sync SDK client if remote options are configured, else ``None``.

    Priority:
    1. ``--langflow-url`` / ``LANGFLOW_URL`` -- direct URL (with optional ``--langflow-api-key``)
    2. ``--langflow-env`` / ``LANGFLOW_ENV`` -- named environment from TOML/YAML file
    """
    url: str | None = request.config.getoption("langflow_url", default=None) or os.environ.get("LANGFLOW_URL")
    env_name: str | None = request.config.getoption("langflow_env", default=None) or os.environ.get("LANGFLOW_ENV")

    if not url and not env_name:
        return None

    try:
        import langflow_sdk  # type: ignore[import-untyped]
    except ImportError:
        pytest.skip("langflow-sdk is required for remote testing. Install: pip install langflow-sdk")

    if url:
        api_key: str | None = request.config.getoption("langflow_api_key", default=None) or os.environ.get(
            "LANGFLOW_API_KEY"
        )
        return langflow_sdk.Client(base_url=url, api_key=api_key)

    # Named environment
    env_file: str | None = request.config.getoption("langflow_environments_file", default=None) or os.environ.get(
        "LANGFLOW_ENVIRONMENTS_FILE"
    )
    try:
        from pathlib import Path as _Path

        from langflow_sdk.environments import get_client  # type: ignore[import-untyped]

        return get_client(env_name, config_file=_Path(env_file) if env_file else None)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Could not configure Langflow environment {env_name!r}: {exc}")