def parse_args() -> List[str]:
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        display_usage()
        sys.exit(0)

    return sys.argv[1:]