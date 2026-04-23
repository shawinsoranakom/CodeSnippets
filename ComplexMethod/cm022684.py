async def test_format_version() -> None:
    """Test format_version method."""
    assert format_version("soho+3.6.8+soho-release-rt120+10") == "3.6.8"
    assert format_version("undefined-undefined-1.6.8") == "1.6.8"
    assert format_version("56.0-76060") == "56.0.76060"
    assert format_version(3.6) == "3.6"
    assert format_version("AK001-ZJ100") == "1.100"
    assert format_version("HF-LPB100-") == "100"
    assert format_version("AK001-ZJ2149") == "1.2149"
    assert format_version("13216407885") == "4294967295"  # max value
    assert format_version("000132 16407885") == "132.16407885"
    assert format_version("0.1") == "0.1"
    assert format_version("0") is None
    assert format_version("unknown") is None