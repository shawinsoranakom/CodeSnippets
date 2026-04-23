def ui(
    host: str = "127.0.0.1",
    port: int = 8081,
    workers: int = 1,
    reload: Annotated[bool, typer.Option("--reload")] = False,
    docs: bool = True,
    appdir: str | None = None,
    database_uri: Optional[str] = None,
    auth_config: Optional[str] = None,
    upgrade_database: bool = False,
):
    """
    Run the AutoGen Studio UI.

    Args:
        host (str, optional): Host to run the UI on. Defaults to 127.0.0.1 (localhost).
        port (int, optional): Port to run the UI on. Defaults to 8081.
        workers (int, optional): Number of workers to run the UI with. Defaults to 1.
        reload (bool, optional): Whether to reload the UI on code changes. Defaults to False.
        docs (bool, optional): Whether to generate API docs. Defaults to False.
        appdir (str, optional): Path to the AutoGen Studio app directory. Defaults to None.
        database_uri (str, optional): Database URI to connect to. Defaults to None.
        auth_config (str, optional): Path to authentication configuration YAML. Defaults to None.
        upgrade_database (bool, optional): Whether to upgrade the database. Defaults to False.
    """
    # Write configuration
    env_vars = {
        "AUTOGENSTUDIO_HOST": host,
        "AUTOGENSTUDIO_PORT": port,
        "AUTOGENSTUDIO_API_DOCS": str(docs),
    }

    if appdir:
        env_vars["AUTOGENSTUDIO_APPDIR"] = appdir
    if database_uri:
        env_vars["AUTOGENSTUDIO_DATABASE_URI"] = database_uri
    if auth_config:
        if not os.path.exists(auth_config):
            typer.echo(f"Error: Auth config file not found: {auth_config}", err=True)
            raise typer.Exit(1)
        env_vars["AUTOGENSTUDIO_AUTH_CONFIG"] = auth_config
    if upgrade_database:
        env_vars["AUTOGENSTUDIO_UPGRADE_DATABASE"] = "1"

    # Create temporary env file to share configuration with uvicorn workers
    env_file_path = get_env_file_path()
    with open(env_file_path, "w") as temp_env:
        for key, value in env_vars.items():
            temp_env.write(f"{key}={value}\n")

    uvicorn.run(
        "autogenstudio.web.app:app",
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        reload_excludes=["**/alembic/*", "**/alembic.ini", "**/versions/*"] if reload else None,
        env_file=env_file_path,
    )