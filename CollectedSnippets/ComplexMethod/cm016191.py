def create_build_plan() -> list[tuple[str, str]]:
    output = check_output(
        ["ninja", "-j1", "-v", "-n", "torch_python"], cwd=str(BUILD_DIR)
    )
    rc = []
    for line in output.split("\n"):
        if not line.startswith("["):
            continue
        line = line.split("]", 1)[1].strip()
        if line.startswith(": &&") and line.endswith("&& :"):
            line = line[4:-4]
        line = line.replace("-O2", "-g").replace("-O3", "-g")
        # Build Metal shaders with debug information
        if "xcrun metal " in line and "-frecord-sources" not in line:
            line += " -frecord-sources -gline-tables-only"
        try:
            name = line.split("-o ", 1)[1].split(" ")[0]
            rc.append((name, line))
        except IndexError:
            print(f"Skipping {line} as it does not specify output file")
    return rc