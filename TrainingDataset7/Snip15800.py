def test_testserver_handle_params(self, mock_handle):
        out = StringIO()
        call_command("testserver", "blah.json", stdout=out)
        mock_handle.assert_called_with(
            "blah.json",
            stdout=out,
            settings=None,
            pythonpath=None,
            verbosity=1,
            traceback=False,
            addrport="",
            no_color=False,
            use_ipv6=False,
            skip_checks=True,
            interactive=True,
            force_color=False,
        )