def parse_dockerfile_args(dockerfile_path: Path) -> dict[str, str]:
    """Extract all ARG defaults from Dockerfile using dockerfile-parse."""
    parser = DockerfileParser(path=str(dockerfile_path))

    # Extract ARGs from structure (more reliable for multi-stage Dockerfiles)
    args = {}
    for item in parser.structure:
        if item["instruction"] != "ARG":
            continue

        value = item["value"]
        if "=" not in value:
            continue

        # Parse ARG NAME=value (handle quotes)
        name, _, default = value.partition("=")
        name = name.strip()

        if name in args:
            # Keep first occurrence
            continue

        # Strip surrounding quotes if present
        default = default.strip()
        if (default.startswith('"') and default.endswith('"')) or (
            default.startswith("'") and default.endswith("'")
        ):
            default = default[1:-1]

        if default:
            args[name] = default

    # Resolve variable interpolation (e.g., ${CUDA_VERSION} -> 12.9.1)
    resolved = {}
    for name, value in args.items():
        if "${" in value:
            # Substitute ${VAR} references with their values
            for ref_name, ref_value in args.items():
                value = value.replace(f"${{{ref_name}}}", ref_value)
        # Skip if still has unresolved references (no default available)
        if "${" not in value:
            resolved[name] = value

    return resolved