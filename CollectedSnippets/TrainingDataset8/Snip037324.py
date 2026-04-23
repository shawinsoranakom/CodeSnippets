def _maybe_print_use_warning() -> None:
    """Print a warning if Streamlit is imported but not being run with `streamlit run`.
    The warning is printed only once, and is printed using the root logger.
    """
    global _use_warning_has_been_displayed

    if not _use_warning_has_been_displayed:
        _use_warning_has_been_displayed = True

        warning = click.style("Warning:", bold=True, fg="yellow")

        if env_util.is_repl():
            logger.get_logger("root").warning(
                f"\n  {warning} to view a Streamlit app on a browser, use Streamlit in a file and\n  run it with the following command:\n\n    streamlit run [FILE_NAME] [ARGUMENTS]"
            )

        elif not runtime.exists() and config.get_option(
            "global.showWarningOnDirectExecution"
        ):
            script_name = sys.argv[0]

            logger.get_logger("root").warning(
                f"\n  {warning} to view this Streamlit app on a browser, run it with the following\n  command:\n\n    streamlit run {script_name} [ARGUMENTS]"
            )