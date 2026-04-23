def test_name(self, HttpApiAuth, add_chat_assistants, payload, expected_code, expected_message):
        _, _, chat_assistant_ids = add_chat_assistants
        if payload["name"] == "duplicated_name":
            create_session_with_chat_assistant(HttpApiAuth, chat_assistant_ids[0], payload)
        elif payload["name"] == "case insensitive":
            create_session_with_chat_assistant(HttpApiAuth, chat_assistant_ids[0], {"name": payload["name"].upper()})

        res = create_session_with_chat_assistant(HttpApiAuth, chat_assistant_ids[0], payload)
        assert res["code"] == expected_code, res
        if expected_code == 0:
            assert res["data"]["name"] == payload["name"]
            assert res["data"]["chat_id"] == chat_assistant_ids[0]
        else:
            assert res["message"] == expected_message