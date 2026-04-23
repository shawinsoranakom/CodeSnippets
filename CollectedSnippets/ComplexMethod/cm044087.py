def import_app(app_path: str, name: str = "app", factory: bool = False):
    """Import the FastAPI app instance from a local file or module."""
    # pylint: disable=import-outside-toplevel
    from fastapi.middleware.cors import CORSMiddleware  # noqa
    from importlib import import_module, util
    from openbb_core.api.app_loader import AppLoader
    from openbb_core.api.rest_api import system

    def _is_module_colon_notation(app_path: str) -> bool:
        """Check if the path uses module:name notation vs a Windows path."""
        if ":" not in app_path:
            return False
        # Windows absolute path check (e.g., C:\path or D:/path)
        if len(app_path) >= 2 and app_path[1] == ":" and app_path[0].isalpha():
            # Could still have colon notation: C:\path\file.py:app
            parts = app_path.split(":")
            return len(parts) > 2  # More than just drive letter colon
        return True

    def _load_module_from_file_path(file_path: str):
        spec_name = os.path.basename(file_path).split(".")[0]
        spec = util.spec_from_file_location(spec_name, file_path)

        if spec is None:
            raise RuntimeError(f"Failed to load the file specs for '{file_path}'")

        module = util.module_from_spec(spec)  # type: ignore
        sys.modules[spec_name] = module  # type: ignore
        spec.loader.exec_module(module)  # type: ignore
        return module

    if _is_module_colon_notation(app_path):
        module_path, name = app_path.rsplit(":", 1)
        try:  # First try to import as a module
            module = import_module(module_path)
        except ImportError:  # If module import fails, try to load as a local file
            if not module_path.endswith(".py"):
                module_path += ".py"

            if not Path(module_path).is_absolute():
                cwd = Path.cwd()
                file_path = str(cwd.joinpath(module_path).resolve())
            else:
                file_path = module_path

            if not Path(file_path).exists():
                raise FileNotFoundError(  # pylint: disable=raise-missing-from
                    f"Error: Neither module '{module_path}' could be imported nor file '{file_path}' exists"
                )

            module = _load_module_from_file_path(file_path)

    # Case 2: File path (e.g., "main.py" or "my_app/main.py")
    else:
        if not Path(app_path).is_absolute():
            cwd = Path.cwd()
            app_path = str(cwd.joinpath(app_path).resolve())

        if not Path(app_path).exists():
            raise FileNotFoundError(f"Error: The app file '{app_path}' does not exist")

        module = _load_module_from_file_path(app_path)

    if not hasattr(module, name):
        raise AttributeError(
            f"Error: The app file '{app_path}' does not contain an '{name}' instance"
        )

    app_or_factory = getattr(module, name)

    # Here we use the same approach as uvicorn to handle factory functions.
    # This prevents us from relying on explicit type annotations.
    # See: https://github.com/encode/uvicorn/blob/master/uvicorn/config.py
    try:
        app = app_or_factory()
        if not factory:
            print(  # noqa: T201
                "\n\n[WARNING]   "
                "App factory detected. Using it, but please consider setting the --factory flag explicitly.\n"
            )
    except TypeError:
        if factory:
            raise TypeError(  # pylint: disable=raise-missing-from
                f"Error: The {name} instance in '{app_path}' appears not to be a callable factory function"
            )
        app = app_or_factory

    if not isinstance(app, FastAPI):
        raise TypeError(
            f"Error: The {name} instance in '{app_path}' is not an instance of FastAPI"
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=system.api_settings.cors.allow_origins,
        allow_methods=system.api_settings.cors.allow_methods,
        allow_headers=system.api_settings.cors.allow_headers,
    )

    AppLoader.add_exception_handlers(app)

    return app