def test_basic_scenarios(
        self,
        HttpApiAuth,
        add_sessions_with_chat_assistant_func,
        payload,
        expected_code,
        expected_message,
        remaining,
    ):
        chat_assistant_id, session_ids = add_sessions_with_chat_assistant_func
        if callable(payload):
            payload = payload(session_ids)
        res = delete_session_with_chat_assistants(HttpApiAuth, chat_assistant_id, payload)
        assert res["code"] == expected_code
        if res["code"] != 0:
            assert res["message"] == expected_message

        res = list_session_with_chat_assistants(HttpApiAuth, chat_assistant_id)
        if res["code"] != 0:
            assert False, res
        assert len(res["data"]) == remaining