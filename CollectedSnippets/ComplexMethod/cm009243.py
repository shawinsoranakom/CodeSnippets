def test_web_fetch() -> None:
    """Note: this is a beta feature.

    TODO: Update to remove beta once it's generally available.
    """
    llm = ChatAnthropic(
        model=MODEL_NAME,  # type: ignore[call-arg]
        max_tokens=1024,
        betas=["web-fetch-2025-09-10"],
    )
    tool = {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 1}
    llm_with_tools = llm.bind_tools([tool])

    input_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Fetch the content at https://docs.langchain.com and analyze",
            },
        ],
    }
    response = llm_with_tools.invoke([input_message])
    assert all(isinstance(block, dict) for block in response.content)
    block_types = {
        block["type"] for block in response.content if isinstance(block, dict)
    }

    # A successful fetch call should include:
    # 1. text response from the model (e.g. "I'll fetch that for you")
    # 2. server_tool_use block indicating the tool was called (using tool "web_fetch")
    # 3. web_fetch_tool_result block with the results of said fetch
    assert block_types == {"text", "server_tool_use", "web_fetch_tool_result"}

    # Verify web fetch result structure
    web_fetch_results = [
        block
        for block in response.content
        if isinstance(block, dict) and block.get("type") == "web_fetch_tool_result"
    ]
    assert len(web_fetch_results) == 1  # Since max_uses=1
    fetch_result = web_fetch_results[0]
    assert "content" in fetch_result
    assert "url" in fetch_result["content"]
    assert "retrieved_at" in fetch_result["content"]

    # Fetch with citations enabled
    tool_with_citations = tool.copy()
    tool_with_citations["citations"] = {"enabled": True}
    llm_with_citations = llm.bind_tools([tool_with_citations])

    citation_message = {
        "role": "user",
        "content": (
            "Fetch https://docs.langchain.com and provide specific quotes with "
            "citations"
        ),
    }
    citation_response = llm_with_citations.invoke([citation_message])

    citation_results = [
        block
        for block in citation_response.content
        if isinstance(block, dict) and block.get("type") == "web_fetch_tool_result"
    ]
    assert len(citation_results) == 1  # Since max_uses=1
    citation_result = citation_results[0]
    assert citation_result["content"]["content"]["citations"]["enabled"]
    text_blocks = [
        block
        for block in citation_response.content
        if isinstance(block, dict) and block.get("type") == "text"
    ]

    # Check that the response contains actual citations in the content
    has_citations = False
    for block in text_blocks:
        citations = block.get("citations", [])
        for citation in citations:
            if citation.get("type") and citation.get("start_char_index"):
                has_citations = True
                break
    assert has_citations, (
        "Expected inline citation tags in response when citations are enabled for "
        "web fetch"
    )

    # Max content tokens param
    tool_with_limit = tool.copy()
    tool_with_limit["max_content_tokens"] = 1000
    llm_with_limit = llm.bind_tools([tool_with_limit])

    limit_response = llm_with_limit.invoke([input_message])
    # Response should still work even with content limits
    assert any(
        block["type"] == "web_fetch_tool_result"
        for block in limit_response.content
        if isinstance(block, dict)
    )

    # Domains filtering (note: only one can be set at a time)
    tool_with_allowed_domains = tool.copy()
    tool_with_allowed_domains["allowed_domains"] = ["docs.langchain.com"]
    llm_with_allowed = llm.bind_tools([tool_with_allowed_domains])

    allowed_response = llm_with_allowed.invoke([input_message])
    assert any(
        block["type"] == "web_fetch_tool_result"
        for block in allowed_response.content
        if isinstance(block, dict)
    )

    # Test that a disallowed domain doesn't work
    tool_with_disallowed_domains = tool.copy()
    tool_with_disallowed_domains["allowed_domains"] = [
        "example.com"
    ]  # Not docs.langchain.com
    llm_with_disallowed = llm.bind_tools([tool_with_disallowed_domains])

    disallowed_response = llm_with_disallowed.invoke([input_message])

    # We should get an error result since the domain (docs.langchain.com) is not allowed
    disallowed_results = [
        block
        for block in disallowed_response.content
        if isinstance(block, dict) and block.get("type") == "web_fetch_tool_result"
    ]
    if disallowed_results:
        disallowed_result = disallowed_results[0]
        if disallowed_result.get("content", {}).get("type") == "web_fetch_tool_error":
            assert disallowed_result["content"]["error_code"] in [
                "invalid_url",
                "fetch_failed",
            ]

    # Blocked domains filtering
    tool_with_blocked_domains = tool.copy()
    tool_with_blocked_domains["blocked_domains"] = ["example.com"]
    llm_with_blocked = llm.bind_tools([tool_with_blocked_domains])

    blocked_response = llm_with_blocked.invoke([input_message])
    assert any(
        block["type"] == "web_fetch_tool_result"
        for block in blocked_response.content
        if isinstance(block, dict)
    )

    # Test fetching from a blocked domain fails
    blocked_domain_message = {
        "role": "user",
        "content": "Fetch https://example.com and analyze",
    }
    tool_with_blocked_example = tool.copy()
    tool_with_blocked_example["blocked_domains"] = ["example.com"]
    llm_with_blocked_example = llm.bind_tools([tool_with_blocked_example])

    blocked_domain_response = llm_with_blocked_example.invoke([blocked_domain_message])

    # Should get an error when trying to access a blocked domain
    blocked_domain_results = [
        block
        for block in blocked_domain_response.content
        if isinstance(block, dict) and block.get("type") == "web_fetch_tool_result"
    ]
    if blocked_domain_results:
        blocked_result = blocked_domain_results[0]
        if blocked_result.get("content", {}).get("type") == "web_fetch_tool_error":
            assert blocked_result["content"]["error_code"] in [
                "invalid_url",
                "fetch_failed",
            ]

    # Max uses parameter - test exceeding the limit
    multi_fetch_message = {
        "role": "user",
        "content": (
            "Fetch https://docs.langchain.com and then try to fetch "
            "https://langchain.com"
        ),
    }
    max_uses_response = llm_with_tools.invoke([multi_fetch_message])

    # Should contain at least one fetch result and potentially an error for the second
    fetch_results = [
        block
        for block in max_uses_response.content
        if isinstance(block, dict) and block.get("type") == "web_fetch_tool_result"
    ]  # type: ignore[index]
    assert len(fetch_results) >= 1
    error_results = [
        r
        for r in fetch_results
        if r.get("content", {}).get("type") == "web_fetch_tool_error"
    ]
    if error_results:
        assert any(
            r["content"]["error_code"] == "max_uses_exceeded" for r in error_results
        )

    # Streaming
    full: BaseMessageChunk | None = None
    for chunk in llm_with_tools.stream([input_message]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert isinstance(full.content, list)
    block_types = {block["type"] for block in full.content if isinstance(block, dict)}
    assert block_types == {"text", "server_tool_use", "web_fetch_tool_result"}

    # Test that URLs from context can be used in follow-up
    next_message = {
        "role": "user",
        "content": "What does the site you just fetched say about models?",
    }
    follow_up_response = llm_with_tools.invoke(
        [input_message, full, next_message],
    )
    # Should work without issues since URL was already in context
    assert isinstance(follow_up_response.content, (list, str))

    # Error handling - test with an invalid URL format
    error_message = {
        "role": "user",
        "content": "Try to fetch this invalid URL: not-a-valid-url",
    }
    error_response = llm_with_tools.invoke([error_message])

    # Should handle the error gracefully
    assert isinstance(error_response.content, (list, str))

    # PDF document fetching
    pdf_message = {
        "role": "user",
        "content": (
            "Fetch this PDF: "
            "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf "
            "and summarize its content",
        ),
    }
    pdf_response = llm_with_tools.invoke([pdf_message])

    assert any(
        block["type"] == "web_fetch_tool_result"
        for block in pdf_response.content
        if isinstance(block, dict)
    )

    # Verify PDF content structure (should have base64 data for PDFs)
    pdf_results = [
        block
        for block in pdf_response.content
        if isinstance(block, dict) and block.get("type") == "web_fetch_tool_result"
    ]
    if pdf_results:
        pdf_result = pdf_results[0]
        content = pdf_result.get("content", {})
        if content.get("content", {}).get("source", {}).get("type") == "base64":
            assert content["content"]["source"]["media_type"] == "application/pdf"
            assert "data" in content["content"]["source"]