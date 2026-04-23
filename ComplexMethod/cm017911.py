def test_deeply_nested_html_fallback() -> None:
    """Large, deeply nested HTML should fall back to plain-text extraction
    instead of silently returning unconverted HTML (issue #1636).

    Note: This test uses sys.setrecursionlimit to guarantee a RecursionError
    regardless of the host environment's default limit, making it deterministic
    across different platforms and CI configurations.
    """
    import sys
    import warnings

    markitdown = MarkItDown()

    # Use a small recursion limit so the test is environment-independent.
    # We restore the original limit in a finally block to avoid side-effects.
    original_limit = sys.getrecursionlimit()
    low_limit = 200  # well below markdownify's traversal depth for depth=500

    # Build HTML with nesting deep enough to trigger RecursionError
    depth = 500
    html = "<html><body>"
    for _ in range(depth):
        html += '<div style="margin-left:10px">'
    html += "<p>Deep content with <b>bold text</b></p>"
    for _ in range(depth):
        html += "</div>"
    html += "</body></html>"

    try:
        sys.setrecursionlimit(low_limit)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = markitdown.convert_stream(
                io.BytesIO(html.encode("utf-8")),
                file_extension=".html",
            )

            # Should have emitted a warning about the fallback
            recursion_warnings = [x for x in w if "deeply nested" in str(x.message)]
            assert len(recursion_warnings) > 0
    finally:
        sys.setrecursionlimit(original_limit)

    # The output should contain the text content, not raw HTML
    assert "Deep content" in result.markdown
    assert "bold text" in result.markdown
    assert "<div" not in result.markdown
    assert "<p>" not in result.markdown