def test_id(self, HttpApiAuth, add_sessions_with_chat_assistant, session_id, expected_code, expected_num, expected_message):
        chat_assistant_id, session_ids = add_sessions_with_chat_assistant
        if callable(session_id):
            params = {"id": session_id(session_ids)}
        else:
            params = {"id": session_id}

        res = list_session_with_chat_assistants(HttpApiAuth, chat_assistant_id, params=params)
        assert res["code"] == expected_code
        if expected_code == 0:
            if params["id"] == session_ids[0]:
                assert res["data"][0]["id"] == params["id"]
            else:
                assert len(res["data"]) == expected_num
        else:
            assert res["message"] == expected_message