def test_llm(self, HttpApiAuth, add_chunks, llm, expected_code, expected_message):
        dataset_id, _, _ = add_chunks
        payload = {"name": "llm_test", "dataset_ids": [dataset_id]}
        if "model_name" in llm:
            payload["llm_id"] = llm["model_name"]
        if any(k != "model_name" for k in llm):
            payload["llm_setting"] = {k: v for k, v in llm.items() if k != "model_name"}
        res = create_chat_assistant(HttpApiAuth, payload)
        assert res["code"] == expected_code
        if expected_code == 0:
            if llm:
                for k, v in llm.items():
                    if k == "model_name":
                        assert res["data"]["llm_id"] == v
                    else:
                        assert res["data"]["llm_setting"][k] == v
            else:
                assert res["data"]["llm_id"] == "glm-4-flash@ZHIPU-AI"
                assert res["data"]["llm_setting"] == {}
        else:
            assert res["message"] == expected_message