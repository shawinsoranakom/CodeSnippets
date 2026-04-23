def test_normalize_agent_settings_fills_base_url_for_all_providers():
    """Managed and BYOR providers should keep usable base URLs in diffs."""
    openhands_null = OrgUpdate.model_validate(
        {
            'agent_settings_diff': {
                'llm': {'model': 'openhands/claude-3', 'base_url': None},
            },
        }
    )
    openhands_missing = OrgUpdate.model_validate(
        {'agent_settings_diff': {'llm': {'model': 'openhands/claude-3'}}}
    )
    anthropic_null = OrgUpdate.model_validate(
        {
            'agent_settings_diff': {
                'llm': {'model': 'anthropic/claude-3-opus-20240229', 'base_url': None},
            },
        }
    )

    openhands_null_diff = openhands_null.agent_settings_diff
    assert openhands_null_diff is not None
    assert openhands_null_diff['llm']['model'] == 'openhands/claude-3'
    assert openhands_null_diff['llm']['base_url'].rstrip('/') == (
        LITE_LLM_API_URL.rstrip('/')
    )

    openhands_missing_diff = openhands_missing.agent_settings_diff
    assert openhands_missing_diff is not None
    assert openhands_missing_diff['llm']['model'] == 'openhands/claude-3'
    assert openhands_missing_diff['llm']['base_url'].rstrip('/') == (
        LITE_LLM_API_URL.rstrip('/')
    )

    anthropic_diff = anthropic_null.agent_settings_diff
    assert anthropic_diff is not None
    anthropic_base = anthropic_diff['llm']['base_url']
    assert isinstance(anthropic_base, str)
    assert 'anthropic.com' in anthropic_base