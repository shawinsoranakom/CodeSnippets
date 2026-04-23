def test_has_exact_mention():
    # Test basic exact match
    assert has_exact_mention('Hello @openhands!', '@openhands') is True
    assert has_exact_mention('@openhands at start', '@openhands') is True
    assert has_exact_mention('End with @openhands', '@openhands') is True
    assert has_exact_mention('@openhands', '@openhands') is True

    # Test no match
    assert has_exact_mention('No mention here', '@openhands') is False
    assert has_exact_mention('', '@openhands') is False

    # Test partial matches (should be False)
    assert has_exact_mention('Hello @openhands-agent!', '@openhands') is False
    assert has_exact_mention('Email: user@openhands.com', '@openhands') is False
    assert has_exact_mention('Text@openhands', '@openhands') is False
    assert has_exact_mention('@openhandsmore', '@openhands') is False

    # Test with special characters in mention
    assert has_exact_mention('Hi @open.hands!', '@open.hands') is True
    assert has_exact_mention('Using @open-hands', '@open-hands') is True
    assert has_exact_mention('With @open_hands_ai', '@open_hands_ai') is True

    # Test case insensitivity (function now handles case conversion internally)
    assert has_exact_mention('Hi @OpenHands', '@OpenHands') is True
    assert has_exact_mention('Hi @OpenHands', '@openhands') is True
    assert has_exact_mention('Hi @openhands', '@OpenHands') is True
    assert has_exact_mention('Hi @OPENHANDS', '@openhands') is True

    # Test multiple mentions
    assert has_exact_mention('@openhands and @openhands again', '@openhands') is True
    assert has_exact_mention('@openhands-agent and @openhands', '@openhands') is True

    # Test with surrounding punctuation
    assert has_exact_mention('Hey, @openhands!', '@openhands') is True
    assert has_exact_mention('(@openhands)', '@openhands') is True
    assert has_exact_mention('@openhands: hello', '@openhands') is True
    assert has_exact_mention('@openhands? yes', '@openhands') is True