def test_report_watchdog_availability_nonmac(self):
        with patch(
            "streamlit.watcher.path_watcher.watchdog_available", new=False
        ), patch("streamlit.env_util.IS_DARWIN", new=False), patch(
            "click.secho"
        ) as mock_echo:
            streamlit.watcher.path_watcher.report_watchdog_availability()

        msg = ""
        calls = [
            call(
                "  %s" % "For better performance, install the Watchdog module:",
                fg="blue",
                bold=True,
            ),
            call(
                """%s
  $ pip install watchdog
            """
                % msg
            ),
        ]
        mock_echo.assert_has_calls(calls)