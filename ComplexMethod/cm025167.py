def run(script_args: list) -> int:
    """Handle check config commandline script."""
    parser = argparse.ArgumentParser(description="Check Home Assistant configuration.")
    parser.add_argument("--script", choices=["check_config"])
    parser.add_argument(
        "-c",
        "--config",
        default=get_default_config_dir(),
        help="Directory that contains the Home Assistant configuration",
    )
    parser.add_argument(
        "-i",
        "--info",
        nargs="?",
        default=None,
        const="all",
        help="Show a portion of the config",
    )
    parser.add_argument(
        "-f", "--files", action="store_true", help="Show used configuration files"
    )
    parser.add_argument(
        "-s", "--secrets", action="store_true", help="Show secret information"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Exit non-zero if warnings are present",
    )

    # Parse all args including --config & --script. Do not use script_args.
    # Example: python -m homeassistant --config "." --script check_config
    args, unknown = parser.parse_known_args()
    if unknown:
        print(color("red", "Unknown arguments:", ", ".join(unknown)))

    config_dir = os.path.join(os.getcwd(), args.config)

    if not args.json:
        print(color("bold", "Testing configuration at", config_dir))

    res = check(config_dir, args.secrets)

    # JSON output branch
    if args.json:
        json_object = {
            "config_dir": config_dir,
            "total_errors": sum(len(errors) for errors in res["except"].values()),
            "total_warnings": sum(len(warnings) for warnings in res["warn"].values()),
            "errors": res["except"],
            "warnings": res["warn"],
            "components": list(res["components"].keys()),
        }

        # Include secrets information if requested
        if args.secrets:
            # Build list of missing secrets (referenced but not found)
            missing_secrets = [
                key for key, val in res["secrets"].items() if val is None
            ]

            # Build list of used secrets (found and used)
            used_secrets = [
                key for key, val in res["secrets"].items() if val is not None
            ]

            json_object["secrets"] = {
                "secret_files": res["secret_cache"],
                "used_secrets": used_secrets,
                "missing_secrets": missing_secrets,
                "total_secrets": len(res["secrets"]),
                "total_missing": len(missing_secrets),
            }

        print(json.dumps(json_object, indent=2))

        # Determine exit code for JSON mode
        return 1 if res["except"] or (args.fail_on_warnings and res["warn"]) else 0

    domain_info: list[str] = []
    if args.info:
        domain_info = args.info.split(",")

    if args.files:
        print(color(C_HEAD, "yaml files"), "(used /", color("red", "not used") + ")")
        deps = os.path.join(config_dir, "deps")
        yaml_files = [
            f
            for f in glob(os.path.join(config_dir, "**/*.yaml"), recursive=True)
            if not f.startswith(deps)
        ]

        for yfn in sorted(yaml_files):
            the_color = "" if yfn in res["yaml_files"] else "red"
            print(color(the_color, "-", yfn))

    if res["except"]:
        print(color("bold_white", "Failed config"))
        for domain, config in res["except"].items():
            domain_info.append(domain)
            print(" ", color("bold_red", domain + ":"), color("red", "", reset="red"))
            dump_dict(config, reset="red")
            print(color("reset"))

    if res["warn"]:
        print(color("bold_white", "Incorrect config"))
        for domain, config in res["warn"].items():
            domain_info.append(domain)
            print(
                " ",
                color("bold_yellow", domain + ":"),
                color("yellow", "", reset="yellow"),
            )
            dump_dict(config, reset="yellow")
            print(color("reset"))

    if domain_info:
        if "all" in domain_info:
            print(color("bold_white", "Successful config (all)"))
            for domain, config in res["components"].items():
                print(" ", color(C_HEAD, domain + ":"))
                dump_dict(config)
        else:
            print(color("bold_white", "Successful config (partial)"))
            for domain in domain_info:
                if domain == ERROR_STR:
                    continue
                print(" ", color(C_HEAD, domain + ":"))
                dump_dict(res["components"].get(domain))

    if args.secrets:
        flatsecret: dict[str, str] = {}

        for sfn, sdict in res["secret_cache"].items():
            sss = []
            for skey in sdict:
                if skey in flatsecret:
                    _LOGGER.error(
                        "Duplicated secrets in files %s and %s", flatsecret[skey], sfn
                    )
                flatsecret[skey] = sfn
                sss.append(color("green", skey) if skey in res["secrets"] else skey)
            print(color(C_HEAD, "Secrets from", sfn + ":"), ", ".join(sss))

        print(color(C_HEAD, "Used Secrets:"))
        for skey, sval in res["secrets"].items():
            if sval is None:
                print(" -", skey + ":", color("red", "not found"))
                continue
            print(" -", skey + ":", sval)

    # Determine final exit code
    return 1 if res["except"] or (args.fail_on_warnings and res["warn"]) else 0