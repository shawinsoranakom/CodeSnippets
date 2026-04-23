def _construct_local_source(
    source_config: dict[str, Any],
    streams: Sequence[str],
    env_vars: dict[str, str] | None = None,
    enforce_method: str | None = None,
    dependency_overrides: list[str] | None = None,
) -> AbstractAirbyteSource:
    with optional_imports("airbyte"):
        from pathway.io.airbyte.logic import (
            FULL_REFRESH_SYNC_MODE,
            INCREMENTAL_SYNC_MODE,
        )
        from pathway.third_party.airbyte_serverless.sources import (
            DockerAirbyteSource,
            VenvAirbyteSource,
        )

    connector_name = source_config["docker_image"].removeprefix("airbyte/")
    connector_name, _, _ = connector_name.partition(":")
    source: AbstractAirbyteSource
    if enforce_method != METHOD_DOCKER and (
        _pip_package_exists(f"airbyte-{connector_name}")
        or enforce_method == METHOD_PYPI
    ):
        logging.info(
            f"The connector {connector_name} was implemented in Python, "
            "running it in the isolated virtual environment"
        )
        source = VenvAirbyteSource(
            connector=connector_name,
            config=source_config.get("config"),
            streams=streams,
            env_vars=copy.copy(env_vars),
            dependency_overrides=dependency_overrides,
        )
    else:
        logging.info(f"Running connector {connector_name} as a Docker image")
        source = DockerAirbyteSource(
            connector=source_config["docker_image"],
            config=source_config.get("config"),
            streams=streams,
            env_vars=copy.copy(env_vars),
        )

    # Run airbyte connector locally and check streams
    global_sync_mode = None
    for stream in source.configured_catalog["streams"]:
        name = stream["stream"]["name"]
        sync_mode = stream["sync_mode"]
        if sync_mode != INCREMENTAL_SYNC_MODE and sync_mode != FULL_REFRESH_SYNC_MODE:
            raise ValueError(f"Stream {name} has unknown sync_mode: {sync_mode}")
        global_sync_mode = global_sync_mode or sync_mode
        if global_sync_mode != sync_mode:
            raise ValueError(
                "All streams within the same 'pw.io.airbyte.read' must have "
                "the same 'sync_mode'"
            )

    return source