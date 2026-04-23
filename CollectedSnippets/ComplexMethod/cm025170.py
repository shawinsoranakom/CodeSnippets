def run(args: list[str]) -> int:
    """Run a script."""
    scripts = []
    path = os.path.dirname(__file__)
    for fil in os.listdir(path):
        if fil == "__pycache__":
            continue

        if os.path.isdir(os.path.join(path, fil)):
            scripts.append(fil)
        elif fil != "__init__.py" and fil.endswith(".py"):
            scripts.append(fil[:-3])

    if not args:
        print("Please specify a script to run.")
        print("Available scripts:", ", ".join(scripts))
        return 1

    if args[0] not in scripts:
        print("Invalid script specified.")
        print("Available scripts:", ", ".join(scripts))
        return 1

    script = importlib.import_module(f"homeassistant.scripts.{args[0]}")

    config_dir = extract_config_dir()

    if not is_virtual_env():
        asyncio.run(async_mount_local_lib_path(config_dir))

    _pip_kwargs = pip_kwargs(config_dir)

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    for req in getattr(script, "REQUIREMENTS", []):
        if is_installed(req):
            continue

        if not install_package(req, **_pip_kwargs):
            print("Aborting script, could not install dependency", req)
            return 1

    asyncio.set_event_loop_policy(runner.HassEventLoopPolicy(False))  # type: ignore[deprecated]

    return script.run(args[1:])