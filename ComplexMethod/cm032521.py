def test_update_mapping_and_validation_branches_p2(self, HttpApiAuth, add_chat_assistants_func, chat_assistant_llm_model_type):
        dataset_id, _, chat_assistant_ids = add_chat_assistants_func
        chat_id = chat_assistant_ids[0]

        # Auth: non-owned chat returns 109 "No authorization."
        res = patch_chat_assistant(HttpApiAuth, "invalid-chat-id", {"name": "anything"})
        assert res["code"] == 109
        assert res["message"] == "No authorization."

        # PATCH: toggle quote via prompt_config
        res = patch_chat_assistant(HttpApiAuth, chat_id, {"prompt_config": {"quote": False}})
        assert res["code"] == 0

        # PATCH: invalid llm_id
        res = patch_chat_assistant(
            HttpApiAuth,
            chat_id,
            {"llm_id": "unknown-llm-model", "llm_setting": {"model_type": chat_assistant_llm_model_type}},
        )
        assert res["code"] == 102
        assert "`llm_id` unknown-llm-model doesn't exist" in res["message"]

        # PATCH: invalid rerank_id
        res = patch_chat_assistant(HttpApiAuth, chat_id, {"rerank_id": "unknown-rerank-model"})
        assert res["code"] == 102
        assert "`rerank_id` unknown-rerank-model doesn't exist" in res["message"]

        # PATCH: empty name
        res = patch_chat_assistant(HttpApiAuth, chat_id, {"name": ""})
        assert res["code"] == 102
        assert res["message"] == "`name` cannot be empty."

        # PATCH: duplicate name
        res = patch_chat_assistant(HttpApiAuth, chat_id, {"name": "test_chat_assistant_1"})
        assert res["code"] == 102
        assert res["message"] == "Duplicated chat name."

        # PATCH: prompt_config without placeholder is allowed
        res = patch_chat_assistant(
            HttpApiAuth,
            chat_id,
            {"prompt_config": {"system": "No required placeholder", "parameters": [{"key": "knowledge", "optional": False}]}},
        )
        assert res["code"] == 0

        # PATCH: icon (was "avatar" in old SDK)
        res = patch_chat_assistant(HttpApiAuth, chat_id, {"icon": "raw-avatar-value"})
        assert res["code"] == 0
        listed = get_chat_assistant(HttpApiAuth, chat_id)
        assert listed["code"] == 0
        assert listed["data"]["icon"] == "raw-avatar-value"