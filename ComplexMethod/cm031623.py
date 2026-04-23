def detect_extension_modules(args: argparse.Namespace) -> dict[str, bool]:
    modules = {}

    # disabled by Modules/Setup.local ?
    with open(args.buildroot / "Makefile") as f:
        for line in f:
            if line.startswith("MODDISABLED_NAMES="):
                disabled = line.split("=", 1)[1].strip().split()
                for modname in disabled:
                    modules[modname] = False
                break

    # disabled by configure?
    with open(args.sysconfig_data) as f:
        data = f.read()
    loc: dict[str, dict[str, str]] = {}
    exec(data, globals(), loc)

    for key, value in loc["build_time_vars"].items():
        if not key.startswith("MODULE_") or not key.endswith("_STATE"):
            continue
        if value not in {"yes", "disabled", "missing", "n/a"}:
            raise ValueError(f"Unsupported value '{value}' for {key}")

        modname = key[7:-6].lower()
        if modname not in modules:
            modules[modname] = value == "yes"
    return modules