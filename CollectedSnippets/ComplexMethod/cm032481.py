def test_llm_setting(self, client, add_chat_assistants_func, llm_setting, expected_message):
        dataset, _, chat_assistants = add_chat_assistants_func
        chat_assistant = chat_assistants[0]
        llm_id = llm_setting.pop("model_name", None)
        payload = {"name": "llm_test", "dataset_ids": [dataset.id], "llm_setting": llm_setting}
        if llm_id is not None:
            payload["llm_id"] = llm_id

        if expected_message:
            with pytest.raises(Exception) as exception_info:
                chat_assistant.update(payload)
            assert expected_message in str(exception_info.value)
        else:
            chat_assistant.update(payload)
            updated_chat = client.get_chat(chat_assistant.id)
            if llm_id:
                assert updated_chat.llm_id == llm_id, str(updated_chat)
            for k, v in llm_setting.items():
                assert getattr(updated_chat.llm_setting, k) == v, str(updated_chat)