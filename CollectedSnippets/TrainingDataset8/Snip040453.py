def parse_args() -> Tuple[str, List[str]]:
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        display_usage()
        sys.exit(0)
    if len(sys.argv) < 3:
        print("Missing arguments")
        display_usage()
        sys.exit(1)
    print(sys.argv)

    return sys.argv[1], sys.argv[2:]