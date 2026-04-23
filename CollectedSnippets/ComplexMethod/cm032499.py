def test_agent_completion_stream_false(self, HttpApiAuth, agent_id):
        res = create_agent_session(HttpApiAuth, agent_id, payload={})
        assert res["code"] == 0, res
        session_id = res["data"]["id"]

        res = agent_completions(
            HttpApiAuth,
            agent_id,
            {"question": "hello", "stream": False, "session_id": session_id},
        )
        assert res["code"] == 0, res
        if isinstance(res["data"], dict):
            assert isinstance(res["data"].get("data"), dict), res
            content = res["data"]["data"].get("content", "")
            assert content, res
            assert "hello" in content, res
            assert res["data"].get("session_id") == session_id, res
        else:
            assert isinstance(res["data"], str), res
            assert res["data"].startswith("**ERROR**"), res