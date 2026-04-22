def report_watchdog_availability():
    if not watchdog_available:
        if not config.get_option("global.disableWatchdogWarning"):
            msg = "\n  $ xcode-select --install" if env_util.IS_DARWIN else ""

            click.secho(
                "  %s" % "For better performance, install the Watchdog module:",
                fg="blue",
                bold=True,
            )
            click.secho(
                """%s
  $ pip install watchdog
            """
                % msg
            )