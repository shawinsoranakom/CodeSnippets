def test_params_to_runserver(
        self, mock_runserver_handle, mock_loaddata_handle, mock_create_test_db
    ):
        call_command("testserver", "blah.json")
        mock_runserver_handle.assert_called_with(
            addrport="",
            force_color=False,
            insecure_serving=False,
            no_color=False,
            pythonpath=None,
            settings=None,
            shutdown_message=(
                "\nServer stopped.\nNote that the test database, 'test_db', "
                "has not been deleted. You can explore it on your own."
            ),
            skip_checks=True,
            traceback=False,
            use_ipv6=False,
            use_reloader=False,
            use_static_handler=True,
            use_threading=connection.features.test_db_allows_multiple_connections,
            verbosity=1,
        )