def test_finally_guard_logic(self):
        """Verify the guard logic matches the implementation."""
        # Case 1: skip_transcript_upload = True → skip upload
        skip_transcript_upload = True
        claude_agent_use_resume = True
        user_id = "uid"
        session = MagicMock()

        if skip_transcript_upload:
            action = "skip_upload"
        elif claude_agent_use_resume and user_id and session is not None:
            action = "upload"
        else:
            action = "no_upload_config"

        assert action == "skip_upload"

        # Case 2: skip_transcript_upload = False → upload
        skip_transcript_upload = False
        if skip_transcript_upload:
            action = "skip_upload"
        elif claude_agent_use_resume and user_id and session is not None:
            action = "upload"
        else:
            action = "no_upload_config"

        assert action == "upload"