def parse_args():  # noqa: PLR0912  # pylint: disable=too-many-branches
    """Parse the launch script command line arguments."""
    args = sys.argv[1:].copy()
    cwd = Path.cwd()
    _kwargs: dict = {}
    for i, arg in enumerate(args):
        if arg == "--help":
            print(LAUNCH_SCRIPT_DESCRIPTION)  # noqa: T201
            sys.exit(0)
        if arg.startswith("--"):
            key = arg[2:]
            if key in ["no-use-colors", "use-colors"]:
                _kwargs["use_colors"] = key == "use-colors"
            elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                value = args[i + 1]
                if isinstance(value, str) and value.lower() in ["false", "true"]:
                    _kwargs[key] = value.lower() == "true"
                elif key == "exclude":
                    _kwargs[key] = json.loads(value)
                else:
                    _kwargs[key] = value
            else:
                _kwargs[key] = True

    if _kwargs.get("app"):
        _app_path = _kwargs.pop("app", None)
        _name = _kwargs.pop("name", "app")
        _factory = _kwargs.pop("factory", False)

        if ":" in _app_path:
            _app_instance_name = _app_path.split(":")[-1]
            _name = _app_instance_name if _app_instance_name else _name

        if _factory and not _name:
            raise ValueError(
                "Error: The factory function name must be provided to the --name parameter when the factory flag is set."
            )
        _kwargs["app"] = import_app(_app_path, _name, _factory)

    if isinstance(_kwargs.get("exclude"), str):
        _kwargs["exclude"] = [_kwargs["exclude"]]

    if _kwargs.get("agents-json") or _kwargs.get("copilots-path"):
        _agents_path = _kwargs.pop("agents-json", None) or _kwargs.pop(
            "copilots-path", None
        )

        if not str(_agents_path).endswith(".json"):
            _agents_path = (
                f"{_agents_path}{'' if _agents_path.endswith('/') else '/'}agents.json"
            )

        if str(_agents_path).startswith("./"):
            _agents_path = str(cwd.joinpath(_agents_path).resolve())

        _kwargs["agents-json"] = _agents_path

    if _kwargs.get("widgets-json") or _kwargs.get("widgets-path"):
        _widgets_path = _kwargs.pop("widgets-json", None) or _kwargs.pop(
            "widgets-path", None
        )

        # If it's a file (endswith .json), use as is; else treat as directory and append widgets.json
        if str(_widgets_path).endswith(".json"):
            widgets_file_path = _widgets_path
        else:
            widgets_file_path = f"{_widgets_path}{'' if str(_widgets_path).endswith('/') else '/'}widgets.json"

        # Resolve relative paths to absolute
        if str(widgets_file_path).startswith("./"):
            widgets_file_path = str(cwd.joinpath(widgets_file_path).resolve())

        _kwargs["widgets-json"] = widgets_file_path

    if _kwargs.get("widgets-json"):
        _kwargs["editable"] = True
        # If the file already exists, we assume that it is already built.
        if os.path.exists(_kwargs["widgets-json"]):
            _kwargs["no-build"] = True

    # Handle apps-json and templates-path in the same way as widgets-path
    if _kwargs.get("apps-json") or _kwargs.get("templates-path"):
        _apps_path = _kwargs.pop("apps-json", None) or _kwargs.pop(
            "templates-path", None
        )

        # If it's a file (endswith .json), use as is; else treat as directory and append apps.json
        if str(_apps_path).endswith(".json"):
            apps_file_path = _apps_path
        else:
            # Check if "workspace_apps.json" exists in the given path
            possible_workspace_file = f"{_apps_path}{'' if str(_apps_path).endswith('/') else '/'}workspace_apps.json"
            if os.path.isfile(possible_workspace_file):
                apps_file_path = possible_workspace_file
            else:
                apps_file_path = f"{_apps_path}{'' if str(_apps_path).endswith('/') else '/'}apps.json"

        # Resolve relative paths to absolute
        if str(apps_file_path).startswith("./"):
            apps_file_path = str(cwd.joinpath(apps_file_path).resolve())

        _kwargs["apps-json"] = apps_file_path

    return _kwargs