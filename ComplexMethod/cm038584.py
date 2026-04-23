def parse_args():
    parser = FlexibleArgumentParser(description="vLLM OpenAI-Compatible batch runner.")
    args = make_arg_parser(parser).parse_args()

    # Backward compatibility: If --url is set, use it for host
    url_explicit = any(arg == "--url" or arg.startswith("--url=") for arg in sys.argv)
    host_explicit = any(
        arg == "--host" or arg.startswith("--host=") for arg in sys.argv
    )
    if url_explicit and hasattr(args, "url") and not host_explicit:
        args.host = args.url
        logger.warning_once(
            "Using --url for metrics is deprecated. Please use --host instead."
        )

    return args