def should_build_library(prefix, name, config, quiet):
    cached_config = prefix / (name + ".json")
    if not cached_config.exists():
        if not quiet:
            print(
                f"No cached build of {name} version {config['version']} found, building"
            )
        return True

    try:
        with cached_config.open("rb") as f:
            cached_config = json.load(f)
    except json.JSONDecodeError:
        if not quiet:
            print(f"Cached data for {name} invalid, rebuilding")
        return True
    if config == cached_config:
        if not quiet:
            print(
                f"Found cached build of {name} version {config['version']}, not rebuilding"
            )
        return False

    if not quiet:
        print(
            f"Found cached build of {name} version {config['version']} but it's out of date, rebuilding"
        )
    return True