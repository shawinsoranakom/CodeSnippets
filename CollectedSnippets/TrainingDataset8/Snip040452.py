def display_usage():
    prog = Path(__file__).name
    print(
        textwrap.dedent(
            f"""\
    usage: {prog} [-h] SUBDIRECTORY ARGS [ARGS ...]

    Runs the program in a subdirectory and fix paths in arguments.

    example:

    When this program is executed with the following command:
       {prog} frontend/ yarn eslint frontend/src/index.ts
    Then the command will be executed:
        yarn eslint src/index.ts
    and the current working directory will be set to frontend/

    positional arguments:
      SUBDIRECTORY  subdirectory within which the subprocess will be executed
      ARGS  sequence of program arguments

    optional arguments:
      -h, --help    show this help message and exit\
    """
        )
    )