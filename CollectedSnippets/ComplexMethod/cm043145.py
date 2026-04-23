async def test_pydantic_configdict():
    """
    Verify no Pydantic deprecation warnings for Config class.

    BEFORE: Used deprecated 'class Config' syntax
    AFTER: Uses ConfigDict for Pydantic v2 compatibility
    """
    print_test("Pydantic v2 ConfigDict", "#678")

    try:
        import pydantic
        from pydantic import __version__ as pydantic_version

        # Capture warnings during import
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", DeprecationWarning)

            # Import models that might have Config classes
            from crawl4ai.models import CrawlResult, MarkdownGenerationResult
            from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig

            # Filter for Pydantic-related deprecation warnings
            pydantic_warnings = [
                warning for warning in w
                if 'pydantic' in str(warning.message).lower()
                or 'config' in str(warning.message).lower()
            ]

            if pydantic_warnings:
                warning_msgs = [str(w.message) for w in pydantic_warnings[:3]]
                record_result("Pydantic ConfigDict", "#678", False,
                             f"Deprecation warnings: {warning_msgs}")
                return

        # Verify models work correctly
        try:
            # Test that models can be instantiated without issues
            config = CrawlerRunConfig()
            browser = BrowserConfig()

            record_result("Pydantic ConfigDict", "#678", True,
                         f"No deprecation warnings with Pydantic v{pydantic_version}")
        except Exception as e:
            record_result("Pydantic ConfigDict", "#678", False,
                         f"Model instantiation failed: {e}")

    except Exception as e:
        record_result("Pydantic ConfigDict", "#678", False, f"Exception: {e}")