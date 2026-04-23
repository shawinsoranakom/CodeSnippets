def test__format_messages_with_cache_control() -> None:
    messages = [
        SystemMessage(
            [
                {"type": "text", "text": "foo", "cache_control": {"type": "ephemeral"}},
            ],
        ),
        HumanMessage(
            [
                {"type": "text", "text": "foo", "cache_control": {"type": "ephemeral"}},
                {
                    "type": "text",
                    "text": "foo",
                },
            ],
        ),
    ]
    expected_system = [
        {"type": "text", "text": "foo", "cache_control": {"type": "ephemeral"}},
    ]
    expected_messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "foo", "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": "foo"},
            ],
        },
    ]
    actual_system, actual_messages = _format_messages(messages)
    assert expected_system == actual_system
    assert expected_messages == actual_messages

    # Test standard multi-modal format (v0)
    messages = [
        HumanMessage(
            [
                {
                    "type": "text",
                    "text": "Summarize this document:",
                },
                {
                    "type": "file",
                    "source_type": "base64",
                    "mime_type": "application/pdf",
                    "data": "<base64 data>",
                    "cache_control": {"type": "ephemeral"},
                },
            ],
        ),
    ]
    actual_system, actual_messages = _format_messages(messages)
    assert actual_system is None
    expected_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Summarize this document:",
                },
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": "<base64 data>",
                    },
                    "cache_control": {"type": "ephemeral"},
                },
            ],
        },
    ]
    assert actual_messages == expected_messages

    # Test standard multi-modal format (v1)
    messages = [
        HumanMessage(
            [
                {
                    "type": "text",
                    "text": "Summarize this document:",
                },
                {
                    "type": "file",
                    "mime_type": "application/pdf",
                    "base64": "<base64 data>",
                    "extras": {"cache_control": {"type": "ephemeral"}},
                },
            ],
        ),
    ]
    actual_system, actual_messages = _format_messages(messages)
    assert actual_system is None
    expected_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Summarize this document:",
                },
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": "<base64 data>",
                    },
                    "cache_control": {"type": "ephemeral"},
                },
            ],
        },
    ]
    assert actual_messages == expected_messages

    # Test standard multi-modal format (v1, unpacked extras)
    messages = [
        HumanMessage(
            [
                {
                    "type": "text",
                    "text": "Summarize this document:",
                },
                {
                    "type": "file",
                    "mime_type": "application/pdf",
                    "base64": "<base64 data>",
                    "cache_control": {"type": "ephemeral"},
                },
            ],
        ),
    ]
    actual_system, actual_messages = _format_messages(messages)
    assert actual_system is None
    expected_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Summarize this document:",
                },
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": "<base64 data>",
                    },
                    "cache_control": {"type": "ephemeral"},
                },
            ],
        },
    ]
    assert actual_messages == expected_messages

    # Also test file inputs
    ## Images
    for block in [
        # v1
        {
            "type": "image",
            "file_id": "abc123",
        },
        # v0
        {
            "type": "image",
            "source_type": "id",
            "id": "abc123",
        },
    ]:
        messages = [
            HumanMessage(
                [
                    {
                        "type": "text",
                        "text": "Summarize this image:",
                    },
                    block,
                ],
            ),
        ]
        actual_system, actual_messages = _format_messages(messages)
        assert actual_system is None
        expected_messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Summarize this image:",
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "file",
                            "file_id": "abc123",
                        },
                    },
                ],
            },
        ]
        assert actual_messages == expected_messages

    ## Documents
    for block in [
        # v1
        {
            "type": "file",
            "file_id": "abc123",
        },
        # v0
        {
            "type": "file",
            "source_type": "id",
            "id": "abc123",
        },
    ]:
        messages = [
            HumanMessage(
                [
                    {
                        "type": "text",
                        "text": "Summarize this document:",
                    },
                    block,
                ],
            ),
        ]
        actual_system, actual_messages = _format_messages(messages)
        assert actual_system is None
        expected_messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Summarize this document:",
                    },
                    {
                        "type": "document",
                        "source": {
                            "type": "file",
                            "file_id": "abc123",
                        },
                    },
                ],
            },
        ]
        assert actual_messages == expected_messages