def test_auto_append_betas_for_mcp_servers() -> None:
    """Test that `mcp-client-2025-11-20` beta is automatically appended
    for `mcp_servers`."""
    model = ChatAnthropic(model=MODEL_NAME)  # type: ignore[call-arg]
    mcp_servers = [
        {
            "type": "url",
            "url": "https://mcp.example.com/mcp",
            "name": "example",
        }
    ]
    payload = model._get_request_payload(
        "Test query",
        mcp_servers=mcp_servers,  # type: ignore[arg-type]
    )
    assert payload["betas"] == ["mcp-client-2025-11-20"]
    assert payload["mcp_servers"] == mcp_servers

    # Test merging with existing betas
    model = ChatAnthropic(
        model=MODEL_NAME,
        betas=["context-management-2025-06-27"],
    )
    payload = model._get_request_payload(
        "Test query",
        mcp_servers=mcp_servers,  # type: ignore[arg-type]
    )
    assert payload["betas"] == [
        "context-management-2025-06-27",
        "mcp-client-2025-11-20",
    ]

    # Test that it doesn't duplicate if beta already present
    model = ChatAnthropic(
        model=MODEL_NAME,
        betas=["mcp-client-2025-11-20"],
    )
    payload = model._get_request_payload(
        "Test query",
        mcp_servers=mcp_servers,  # type: ignore[arg-type]
    )
    assert payload["betas"] == ["mcp-client-2025-11-20"]

    # Test with mcp_servers set on model initialization
    model = ChatAnthropic(
        model=MODEL_NAME,
        mcp_servers=mcp_servers,  # type: ignore[arg-type]
    )
    payload = model._get_request_payload("Test query")
    assert payload["betas"] == ["mcp-client-2025-11-20"]
    assert payload["mcp_servers"] == mcp_servers

    # Test with existing betas and mcp_servers on model initialization
    model = ChatAnthropic(
        model=MODEL_NAME,
        betas=["context-management-2025-06-27"],
        mcp_servers=mcp_servers,  # type: ignore[arg-type]
    )
    payload = model._get_request_payload("Test query")
    assert payload["betas"] == [
        "context-management-2025-06-27",
        "mcp-client-2025-11-20",
    ]

    # Test that beta is not appended when mcp_servers is None
    model = ChatAnthropic(model=MODEL_NAME)
    payload = model._get_request_payload("Test query")
    assert "betas" not in payload or payload["betas"] is None

    # Test combining mcp_servers with tool types that require betas
    model = ChatAnthropic(model=MODEL_NAME)
    tool = {"type": "web_fetch_20250910", "name": "web_fetch"}
    model_with_tools = model.bind_tools([tool])
    payload = model_with_tools._get_request_payload(  # type: ignore[attr-defined]
        "Test query",
        mcp_servers=mcp_servers,
        **model_with_tools.kwargs,  # type: ignore[attr-defined]
    )
    assert set(payload["betas"]) == {
        "web-fetch-2025-09-10",
        "mcp-client-2025-11-20",
    }