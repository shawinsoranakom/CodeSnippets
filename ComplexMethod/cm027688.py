def get_config() -> Config:
    """Return config."""
    parser = argparse.ArgumentParser(description="Hassfest")
    parser.add_argument(
        "--action", type=str, choices=["validate", "generate"], default=None
    )
    parser.add_argument(
        "--integration-path",
        action="append",
        type=valid_integration_path,
        help="Validate a single integration",
    )
    parser.add_argument(
        "--requirements",
        action="store_true",
        help="Validate requirements",
    )
    parser.add_argument(
        "-p",
        "--plugins",
        type=validate_plugins,
        default=ALL_PLUGIN_NAMES,
        help="Comma-separated list of plugins to run. Valid plugin names: %(default)s",
    )
    parser.add_argument(
        "--skip-plugins",
        type=validate_plugins,
        default=[],
        help=f"Comma-separated list of plugins to skip. Valid plugin names: {ALL_PLUGIN_NAMES}",
    )
    parser.add_argument(
        "--core-path",
        type=Path,
        default=Path(),
        help="Path to core",
    )
    parsed = parser.parse_args()

    if parsed.action is None:
        parsed.action = "validate" if parsed.integration_path else "generate"

    if parsed.action == "generate" and parsed.integration_path:
        raise RuntimeError(
            "Generate is not allowed when limiting to specific integrations"
        )

    if (
        not parsed.integration_path
        and not (parsed.core_path / "requirements_all.txt").is_file()
    ):
        raise RuntimeError("Run from Home Assistant root")

    if parsed.skip_plugins:
        parsed.plugins = set(parsed.plugins) - set(parsed.skip_plugins)

    return Config(
        root=parsed.core_path.absolute(),
        specific_integrations=parsed.integration_path,
        action=parsed.action,
        requirements=parsed.requirements,
        plugins=set(parsed.plugins),
    )