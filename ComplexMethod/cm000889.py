async def test_subagent_hooks_sanitize_inputs(_subagent_hooks, caplog):
    """SubagentStart/Stop should sanitize control chars from inputs."""
    start, stop = _subagent_hooks
    # Inject control characters (C0, DEL, C1, BiDi overrides, zero-width)
    # — hook should not raise AND logs must be clean
    with caplog.at_level(logging.DEBUG, logger="backend.copilot.sdk.security_hooks"):
        result = await start(
            {
                "agent_id": "sa\n-injected\r\x00\x7f",
                "agent_type": "safe\x80_type\x9f\ttab",
            },
            tool_use_id=None,
            context={},
        )
    assert result == {}
    # Control chars must be stripped from the logged values
    for record in caplog.records:
        assert "\x00" not in record.message
        assert "\r" not in record.message
        assert "\n" not in record.message
        assert "\x7f" not in record.message
        assert "\x80" not in record.message
        assert "\x9f" not in record.message
    assert "safe_type" in caplog.text

    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="backend.copilot.sdk.security_hooks"):
        result = await stop(
            {
                "agent_id": "sa\n-injected\x7f",
                "agent_type": "type\r\x80\x9f",
                "agent_transcript_path": "/tmp/\x00malicious\npath\u202a\u200b",
            },
            tool_use_id=None,
            context={},
        )
    assert result == {}
    for record in caplog.records:
        assert "\x00" not in record.message
        assert "\r" not in record.message
        assert "\n" not in record.message
        assert "\x7f" not in record.message
        assert "\u202a" not in record.message
        assert "\u200b" not in record.message
    assert "/tmp/maliciouspath" in caplog.text