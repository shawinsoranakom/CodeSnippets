def test_concurrent_create_session(self, HttpApiAuth, add_chat_assistants):
        count = 1000
        _, _, chat_assistant_ids = add_chat_assistants
        res = list_session_with_chat_assistants(HttpApiAuth, chat_assistant_ids[0])
        if res["code"] != 0:
            assert False, res
        sessions_count = len(res["data"])

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(
                    create_session_with_chat_assistant,
                    HttpApiAuth,
                    chat_assistant_ids[0],
                    {"name": f"session with chat assistant test {i}"},
                )
                for i in range(count)
            ]
        responses = list(as_completed(futures))
        assert len(responses) == count, responses
        assert all(future.result()["code"] == 0 for future in futures)
        res = list_session_with_chat_assistants(HttpApiAuth, chat_assistant_ids[0], {"page_size": count * 2})
        if res["code"] != 0:
            assert False, res
        assert len(res["data"]) == sessions_count + count