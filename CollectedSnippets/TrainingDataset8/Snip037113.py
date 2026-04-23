def display_usage():
    print(
        textwrap.dedent(
            f"""\
    usage: {PROG} [-h] [ARGS ...]

    Runs the compose environment for E2E tests

    If additional arguments are passed, it will be executed as a command
    in the environment.

    If no additional arguments are passed, the bash console will be started.

    The script automatically enters the corresponding directory in the container,
    so you can safely pass relatively paths as script arguments.

    example:

    To run a single test, run command:
    ./{PROG} ../scripts/run_e2e_tests.py -u ./specs/st_code.spec.js

    positional arguments:
      ARGS  sequence of program arguments

    optional arguments:
      -h, --help    show this help message and exit\
    """
        )
    )