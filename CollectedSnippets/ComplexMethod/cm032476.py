def test_id(self, add_sessions_with_chat_assistant, session_id, expected_num, expected_message):
        chat_assistant, sessions = add_sessions_with_chat_assistant
        if callable(session_id):
            params = {"id": session_id([s.id for s in sessions])}
        else:
            params = {"id": session_id}

        if expected_message:
            with pytest.raises(Exception) as exception_info:
                chat_assistant.list_sessions(**params)
            assert expected_message in str(exception_info.value)
        else:
            list_sessions = chat_assistant.list_sessions(**params)
            if "id" in params and params["id"] == sessions[0].id:
                assert list_sessions[0].id == params["id"]
            else:
                assert len(list_sessions) == expected_num