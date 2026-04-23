def main() -> int:
    """Scaffold an integration."""
    if not Path("requirements_all.txt").is_file():
        print("Run from project root")
        return 1

    args = get_arguments()

    info = gather_info.gather_info(args)
    print()

    # If we are calling scaffold on a non-existing integration,
    # We're going to first make it. If we're making an integration,
    # we will also make a config flow to go with it.

    if info.is_new:
        generate.generate("integration", info)

        # If it's a new integration and it's not a config flow,
        # create a config flow too.
        if not args.template.startswith("config_flow"):
            if info.integration_type == "helper":
                template = "config_flow_helper"
            elif info.oauth2:
                template = "config_flow_oauth2"
            elif info.authentication or not info.discoverable:
                template = "config_flow"
            else:
                template = "config_flow_discovery"

            generate.generate(template, info)

    # If we wanted a new integration, we've already done our work.
    if args.template != "integration":
        generate.generate(args.template, info)

    # Always output sub commands as the output will contain useful information if a command fails.
    print("Running hassfest to pick up new information.")
    run_process(
        "hassfest",
        [
            "python",
            "-m",
            "script.hassfest",
            "--integration-path",
            str(info.integration_dir),
            "--skip-plugins",
            "quality_scale",  # Skip quality scale as it will fail for newly generated integrations.
        ],
        info,
    )

    print("Running gen_requirements_all to pick up new information.")
    run_process(
        "gen_requirements_all",
        ["python", "-m", "script.gen_requirements_all"],
        info,
    )

    print("Running translations to pick up new translation strings.")
    run_process(
        "translations",
        [
            "python",
            "-m",
            "script.translations",
            "develop",
            "--integration",
            info.domain,
        ],
        info,
    )

    if args.develop:
        print("Running tests")
        run_process(
            "pytest",
            [
                "python3",
                "-b",
                "-m",
                "pytest",
                "-vvv",
                f"tests/components/{info.domain}",
            ],
            info,
        )

    docs.print_relevant_docs(args.template, info)

    return 0