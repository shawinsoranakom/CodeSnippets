def _validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if not args.http and (args.host != "127.0.0.1" or args.port != 8000):
        print(
            "Host and port arguments are only valid when using HTTP transport (see: `--http`).",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.ppocr_source in ["aistudio", "qianfan", "self_hosted"]:
        if not args.server_url:
            print("Error: The server base URL is required.", file=sys.stderr)
            print(
                "Please either set `--server_url` or set the environment variable "
                "`PADDLEOCR_MCP_SERVER_URL`.",
                file=sys.stderr,
            )
            sys.exit(2)

        if args.ppocr_source == "aistudio" and not args.aistudio_access_token:
            print("Error: The AI Studio access token is required.", file=sys.stderr)
            print(
                "Please either set `--aistudio_access_token` or set the environment variable "
                "`PADDLEOCR_MCP_AISTUDIO_ACCESS_TOKEN`.",
                file=sys.stderr,
            )
            sys.exit(2)
        elif args.ppocr_source == "qianfan":
            if not args.qianfan_api_key:
                print("Error: The Qianfan API key is required.", file=sys.stderr)
                print(
                    "Please either set `--qianfan_api_key` or set the environment variable "
                    "`PADDLEOCR_MCP_QIANFAN_API_KEY`.",
                    file=sys.stderr,
                )
                sys.exit(2)
            if args.pipeline not in ("PP-StructureV3", "PaddleOCR-VL"):
                print(
                    f"{repr(args.pipeline)} is currently not supported when using the {repr(args.ppocr_source)} source.",
                    file=sys.stderr,
                )
                sys.exit(2)