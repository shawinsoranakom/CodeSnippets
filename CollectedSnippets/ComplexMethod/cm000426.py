def test_format_onboarding_for_extraction_basic():
    result = format_onboarding_for_extraction(
        user_name="John",
        user_role="Founder/CEO",
        pain_points=["Finding leads", "Email & outreach"],
    )
    assert "Q: What is your name?" in result
    assert "A: John" in result
    assert "Q: What best describes your role?" in result
    assert "A: Founder/CEO" in result
    assert "Q: What tasks are eating your time?" in result
    assert "Finding leads" in result
    assert "Email & outreach" in result