def test_openai_turn_input_logger_writes_html_report(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOGS_PATH", str(tmp_path))

    logger = OpenAITurnInputLogger(model=Llm.GPT_5_2_CODEX_LOW, enabled=True)
    logger.record_turn_input(
        [
            {
                "role": "user",
                "content": "Build this page",
            },
            {
                "type": "function_call",
                "name": "read_file",
                "call_id": "call-1",
                "arguments": '{"path":"/tmp/example.txt"}',
            },
        ]
    )
    logger.record_turn_usage(
        TokenUsage(
            input=1200,
            output=300,
            cache_read=600,
            total=2100,
        )
    )

    report_path = logger.write_html_report()

    assert report_path is not None
    report = Path(report_path)
    assert report.exists()
    assert report.parent == tmp_path / "run_logs"

    html = report.read_text(encoding="utf-8")
    assert "OpenAI Turn Input Report" in html
    assert "Turn 1 (items=2)" in html
    assert "Build this page" in html
    assert "read_file" in html
    assert "Input tokens" in html
    assert "1200" in html
    assert "Cache hit rate" in html
    assert "33.33%" in html
    assert "Cost" in html
    assert "$" in html