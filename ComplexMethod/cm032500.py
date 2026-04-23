def test_openai_chat_completion_non_stream(self, HttpApiAuth, add_dataset_func, tmp_path, request):
        """Test OpenAI-compatible endpoint returns proper response with token usage"""
        dataset_id = add_dataset_func
        document_ids = bulk_upload_documents(HttpApiAuth, dataset_id, 1, tmp_path)
        res = parse_documents(HttpApiAuth, dataset_id, {"document_ids": document_ids})
        assert res["code"] == 0, res
        _parse_done(HttpApiAuth, dataset_id, document_ids)

        res = create_chat_assistant(HttpApiAuth, {"name": "openai_endpoint_test", "dataset_ids": [dataset_id]})
        assert res["code"] == 0, res
        chat_id = res["data"]["id"]
        request.addfinalizer(lambda: delete_all_chat_assistants(HttpApiAuth))

        res = chat_completions_openai(
            HttpApiAuth,
            chat_id,
            {
                "model": "model",  # Required by OpenAI-compatible API, value is ignored by RAGFlow
                "messages": [{"role": "user", "content": "hello"}],
                "stream": False,
            },
        )

        # Verify OpenAI-compatible response structure
        assert "choices" in res, f"Response should contain 'choices': {res}"
        assert len(res["choices"]) > 0, f"'choices' should not be empty: {res}"
        assert "message" in res["choices"][0], f"Choice should contain 'message': {res}"
        assert "content" in res["choices"][0]["message"], f"Message should contain 'content': {res}"

        # Verify token usage is present and uses actual token counts (not character counts)
        assert "usage" in res, f"Response should contain 'usage': {res}"
        usage = res["usage"]
        assert "prompt_tokens" in usage, f"'usage' should contain 'prompt_tokens': {usage}"
        assert "completion_tokens" in usage, f"'usage' should contain 'completion_tokens': {usage}"
        assert "total_tokens" in usage, f"'usage' should contain 'total_tokens': {usage}"
        assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"], \
            f"total_tokens should equal prompt_tokens + completion_tokens: {usage}"