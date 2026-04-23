def parse_args():
    """Parse command line arguments."""
    # pylint: disable=import-outside-toplevel
    from openbb_core.env import Env

    _ = Env()

    args = sys.argv[1:].copy()
    _kwargs: dict = {}

    # Parse all command line arguments into kwargs
    for i, arg in enumerate(args):
        if arg == "--help":
            print(cl_doc)  # noqa: T201
            sys.exit(0)
        if arg.startswith("--"):
            key = arg[2:].replace("-", "_")
            if key in ["no_use_colors", "use_colors"]:
                _kwargs["use_colors"] = key == "use_colors"
            elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                value = args[i + 1]
                if isinstance(value, str) and value.lower() in ["false", "true"]:
                    _kwargs[key] = value.lower() == "true"
                else:
                    try:
                        if (value.startswith("{") and value.endswith("}")) or (
                            value.startswith("[") and value.endswith("]")
                        ):
                            _kwargs[key] = json.loads(value)
                        elif (
                            key != "app"
                            and ":" in value
                            and all(":" in part for part in value.split(","))
                        ):
                            _kwargs[key] = {
                                k.strip(): v.strip()
                                for k, v in (p.split(":", 1) for p in value.split(","))
                            }
                        else:
                            _kwargs[key] = value
                    except (json.JSONDecodeError, ValueError):
                        _kwargs[key] = value
            else:
                _kwargs[key] = True

    # Extract and handle app import arguments
    _app_path = _kwargs.pop("app", None)
    _name = _kwargs.pop("name", "app")
    _factory = _kwargs.pop("factory", False)

    imported_app = None
    if _app_path:
        if ":" in _app_path:
            _app_instance_name = _app_path.split(":")[-1]
            _name = _app_instance_name if _app_instance_name else _name

        if _factory and not _name:
            raise ValueError(
                "Error: The factory function name must be provided to the --name parameter when the factory flag is set."
            )
        imported_app = import_app(_app_path, _name, _factory)

    # Extract MCP-specific arguments
    transport = _kwargs.pop("transport", "streamable-http")
    allowed_categories = _kwargs.pop("allowed_categories", None)
    default_categories = _kwargs.pop("default_categories", "all")
    tool_discovery = _kwargs.pop("tool_discovery", False)
    system_prompt = _kwargs.pop("system_prompt", None)
    server_prompts = _kwargs.pop("server_prompts", None)

    class Args:
        """Container for parsed command line arguments."""

        def __init__(self):
            """Initialize the Args container."""
            self.imported_app = imported_app
            self.transport = transport
            self.allowed_categories = allowed_categories
            self.default_categories = default_categories
            self.tool_discovery = tool_discovery
            self.system_prompt = system_prompt
            self.server_prompts = server_prompts
            self.uvicorn_config = _kwargs  # All remaining kwargs go to uvicorn

    return Args()