def _create_test_session(event_loop: Optional[AbstractEventLoop] = None) -> AppSession:
    """Create an AppSession instance with some default mocked data."""
    if event_loop is None:
        event_loop = MagicMock()

    with patch(
        "streamlit.runtime.app_session.asyncio.get_running_loop",
        return_value=event_loop,
    ):
        return AppSession(
            session_data=SessionData("/fake/script_path.py", "fake_command_line"),
            uploaded_file_manager=MagicMock(),
            message_enqueued_callback=None,
            local_sources_watcher=MagicMock(),
            user_info={"email": "test@test.com"},
        )