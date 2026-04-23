def test_model_prefers_responses_api() -> None:
    # Pro models (with and without date snapshots): Responses API only
    assert _model_prefers_responses_api("gpt-5-pro")
    assert _model_prefers_responses_api("gpt-5-pro-2025-10-06")
    assert _model_prefers_responses_api("gpt-5.2-pro")
    assert _model_prefers_responses_api("gpt-5.2-pro-2025-12-11")
    assert _model_prefers_responses_api("gpt-5.4-pro")
    assert _model_prefers_responses_api("gpt-5.4-pro-2026-03-05")
    # Codex models: Responses API only
    assert _model_prefers_responses_api("gpt-5.3-codex")
    assert _model_prefers_responses_api("gpt-5.2-codex")
    assert _model_prefers_responses_api("gpt-5.1-codex")
    assert _model_prefers_responses_api("gpt-5.1-codex-max")
    assert _model_prefers_responses_api("gpt-5.1-codex-mini")
    assert _model_prefers_responses_api("gpt-5-codex")
    assert _model_prefers_responses_api("codex-mini-latest")
    # These should not match
    assert not _model_prefers_responses_api("gpt-5")
    assert not _model_prefers_responses_api("gpt-5.1")
    assert not _model_prefers_responses_api("gpt-5.4")
    assert not _model_prefers_responses_api("o3-pro")
    assert not _model_prefers_responses_api("gpt-4.1")
    assert not _model_prefers_responses_api(None)