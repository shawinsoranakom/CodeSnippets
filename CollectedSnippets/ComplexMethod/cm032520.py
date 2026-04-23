def test_prompt(self, HttpApiAuth, add_chat_assistants_func, prompt, expected_code, expected_message):
        dataset_id, _, chat_assistant_ids = add_chat_assistants_func

        _PROMPT_CONFIG_KEYS = {"prologue", "quote", "system", "parameters", "empty_response"}

        payload = {"name": "prompt_test", "dataset_ids": [dataset_id]}
        prompt_config = {}
        for k, v in prompt.items():
            if k in _PROMPT_CONFIG_KEYS:
                prompt_config[k] = v
            else:
                payload[k] = v
        if prompt_config:
            payload["prompt_config"] = prompt_config

        res = update_chat_assistant(HttpApiAuth, chat_assistant_ids[0], payload)
        assert res["code"] == expected_code
        if expected_code == 0:
            if not prompt:
                return
            res = get_chat_assistant(HttpApiAuth, chat_assistant_ids[0])
            for k, v in prompt.items():
                if k in _PROMPT_CONFIG_KEYS:
                    assert res["data"]["prompt_config"][k] == v
                else:
                    assert res["data"][k] == v
        else:
            assert expected_message in res["message"]