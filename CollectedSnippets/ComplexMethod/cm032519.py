def test_llm(self, HttpApiAuth, add_chat_assistants_func, chat_assistant_llm_model_type, llm, expected_code, expected_message):
        dataset_id, _, chat_assistant_ids = add_chat_assistants_func
        llm_setting = {k: v for k, v in llm.items() if k != "llm_id"}
        llm_setting.setdefault("model_type", chat_assistant_llm_model_type)

        payload = {"name": "llm_test", "dataset_ids": [dataset_id]}
        if "llm_id" in llm:
            payload["llm_id"] = llm["llm_id"]
        payload["llm_setting"] = llm_setting

        res = update_chat_assistant(HttpApiAuth, chat_assistant_ids[0], payload)
        assert res["code"] == expected_code
        if expected_code == 0:
            res = get_chat_assistant(HttpApiAuth, chat_assistant_ids[0])
            for k, v in llm.items():
                if k == "llm_id":
                    assert res["data"]["llm_id"] == v
                else:
                    assert res["data"]["llm_setting"][k] == v
        else:
            assert expected_message in res["message"]