def test_chat_completion_stream_false_with_session(self, HttpApiAuth, add_dataset_func, tmp_path, request):
        dataset_id = add_dataset_func
        document_ids = bulk_upload_documents(HttpApiAuth, dataset_id, 1, tmp_path)
        res = parse_documents(HttpApiAuth, dataset_id, {"document_ids": document_ids})
        assert res["code"] == 0, res
        _parse_done(HttpApiAuth, dataset_id, document_ids)

        res = create_chat_assistant(HttpApiAuth, {"name": "chat_completion_test", "dataset_ids": [dataset_id]})
        assert res["code"] == 0, res
        chat_id = res["data"]["id"]
        request.addfinalizer(lambda: delete_all_chat_assistants(HttpApiAuth))
        request.addfinalizer(lambda: delete_all_sessions_with_chat_assistant(HttpApiAuth, chat_id))

        res = create_session_with_chat_assistant(HttpApiAuth, chat_id, {"name": "session_for_completion"})
        assert res["code"] == 0, res
        session_id = res["data"]["id"]

        res = chat_completions(
            HttpApiAuth,
            chat_id,
            {
                "messages": [{"role": "user", "content": "hello"}],
                "stream": False,
                "session_id": session_id,
            },
        )
        assert res["code"] == 0, res
        assert isinstance(res["data"], dict), res
        for key in ["answer", "reference", "audio_binary", "id", "session_id"]:
            assert key in res["data"], res
        assert res["data"]["session_id"] == session_id, res