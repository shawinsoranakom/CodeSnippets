def main():
    """
    Main entry function exposed via CLI (e.g. g4f).
    Handles selecting: api / gui / client / mcp
    """
    parser = argparse.ArgumentParser(description="Run gpt4free", exit_on_error=False)
    parser.add_argument("--install-autocomplete", action="store_true", help="Install Bash autocompletion for g4f CLI.")
    args, remaining = parser.parse_known_args()
    if args.install_autocomplete:
        generate_autocomplete()
        return


    mode_parser = ArgumentParser(description="Select mode to run g4f in.", exit_on_error=False)
    mode_parser.add_argument("mode", nargs="?", choices=["api", "gui", "client", "mcp", "auth", "debug"], default="api", help="Mode to run g4f in (default: api).")

    # Preserve original remaining so the API parser gets all args if mode
    # detection fails (e.g. `python -m g4f --port 8080` without a mode prefix).
    original_remaining = remaining
    try:
        try:
            args, remaining = mode_parser.parse_known_args(remaining)
        except argparse.ArgumentError:
            parser = get_api_parser(exit_on_error=False)
            args = parser.parse_args(remaining)
            run_api_args(args)
            return
        if args.mode == "auth":
            parser = get_auth_parser()
            args, remaining = parser.parse_known_args(remaining)
            print(f"Handling auth for provider: {args.provider}, action: {args.action}")
            handle_auth(args.provider, args.action, remaining)
            return
        elif args.mode == "debug":
            parser = get_api_parser()
            args = parser.parse_args(remaining)
            args.debug = True
            args.reload = True
            if args.port is None:
                args.port = 8080
            run_api_args(args)
        elif args.mode == "api":
            parser = get_api_parser()
            args = parser.parse_args(remaining)
            run_api_args(args)
        elif args.mode == "gui":
            parser = gui_parser()
            args = parser.parse_args(remaining)
            run_gui_args(args)
        elif args.mode == "client":
            parser = get_parser()
            args = parser.parse_args(remaining)
            run_client_args(args)
        elif args.mode == "mcp":
            parser = get_mcp_parser()
            args = parser.parse_args(remaining)
            run_mcp_args(args)
        else:
            # No mode provided
            raise argparse.ArgumentError(
                None,
                "No valid mode specified. Use 'api', 'gui', 'client', 'mcp', or 'auth'."
            )

    except argparse.ArgumentError:
        # Try client mode
        run_client_args(
            get_parser(exit_on_error=False).parse_args(),
            exit_on_error=False
        )