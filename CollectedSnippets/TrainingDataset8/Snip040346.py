def _create_mock_app_session(*args, **kwargs):
        """Create a mock AppSession. Each mocked instance will have
        its own unique ID."""
        mock_id = mock.PropertyMock(
            return_value=f"mock_id:{ServerTestCase._next_session_id}"
        )
        ServerTestCase._next_session_id += 1

        mock_session = mock.MagicMock(AppSession, autospec=True, *args, **kwargs)
        type(mock_session).id = mock_id
        return mock_session