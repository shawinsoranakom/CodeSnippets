def add_common_arguments(parser):
    parser.add_argument(
        "-r",
        "--resources",
        action="append",
        help="limit operation to the specified resources",
    )
    parser.add_argument(
        "-l",
        "--languages",
        action="append",
        help="limit operation to the specified languages",
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        default=1,
        type=int,
        choices=[0, 1, 2, 3],
        help=(
            "Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, "
            "3=very verbose output"
        ),
    )