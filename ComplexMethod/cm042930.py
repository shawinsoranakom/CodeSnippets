async def assert_crawl_result_structure(result: Dict[str, Any], check_ssl=False):
    """Asserts the basic structure of a single crawl result."""
    assert isinstance(result, dict)
    assert "url" in result
    assert "success" in result
    assert "html" in result # Basic crawls should return HTML
    assert "metadata" in result
    assert isinstance(result["metadata"], dict)
    assert "depth" in result["metadata"] # Deep crawls add depth

    if check_ssl:
        assert "ssl_certificate" in result # Check if SSL info is present
        assert isinstance(result["ssl_certificate"], dict) or result["ssl_certificate"] is None