def message_from_bytes(s):
    """
    email.message_from_bytes() using modern email.policy.default.
    Returns a modern email.message.EmailMessage.
    """
    # The modern email parser has a bug with adjacent rfc2047 encoded-words.
    # This doesn't affect django.core.mail (which doesn't parse messages),
    # but it can confuse our tests that try to verify sent content by reparsing
    # the generated message. Apply a workaround if needed.
    message = _message_from_bytes(s, policy=policy.default)
    if NEEDS_CPYTHON_128110_WORKAROUND and RFC2047_PREFIX.encode() in s:
        _apply_cpython_128110_workaround(message, s)
    return message