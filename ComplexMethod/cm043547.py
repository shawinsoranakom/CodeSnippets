def main(
    debug: bool,
    dev: bool,
    path_list: list[str],
    routines_args: list[str] | None = None,
    **kwargs,
):
    """Run the CLI with various options.

    Parameters
    ----------
    debug : bool
        Whether to run the CLI in debug mode
    dev:
        Points backend towards development environment instead of production
    test : bool
        Whether to run the CLI in integrated test mode
    filtert : str
        Filter test files with given string in name
    paths : List[str]
        The paths to run for scripts or to test
    verbose : bool
        Whether to show output from tests
    routines_args : List[str]
        One or multiple inputs to be replaced in the routine and separated by commas.
        E.g. GME,AMC,BTC-USD
    """
    if debug:
        session.settings.DEBUG_MODE = True

    if dev:
        session.settings.DEV_BACKEND = True
        session.settings.BASE_URL = "https://payments.openbb.dev/"
        session.settings.HUB_URL = "https://my.openbb.dev"

    if isinstance(path_list, list) and path_list[0].endswith(".openbb"):
        run_routine(
            file=path_list[0],
            routines_args=",".join(routines_args) if routines_args else None,
        )
    elif path_list:
        argv_cmds = list([" ".join(path_list).replace(" /", "/home/")])
        argv_cmds = insert_start_slash(argv_cmds) if argv_cmds else argv_cmds
        run_cli(argv_cmds)
    else:
        run_cli()