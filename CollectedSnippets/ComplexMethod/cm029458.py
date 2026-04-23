def test_openai_turn_input_logger_preserves_full_large_payloads(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("LOGS_PATH", str(tmp_path))

    logger = OpenAITurnInputLogger(model=Llm.GPT_5_3_CODEX_LOW, enabled=True)
    logger.record_turn_input(
        [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": "BEGIN-" + ("x" * 450) + "-END"}],
            }
        ]
    )

    report_path = logger.write_html_report()

    assert report_path is not None
    html = Path(report_path).read_text(encoding="utf-8")
    assert "Usage unavailable for this turn." in html
    assert "Raw JSON payload" in html
    assert "string (460 chars)" in html
    assert "BEGIN-" in html
    assert "-END" in html
    assert "truncated 50 chars" not in html