async def test_browser_context_id_basic():
    """
    Test that BrowserConfig accepts browser_context_id and target_id parameters.
    """
    logger.info("Testing BrowserConfig browser_context_id parameter", tag="TEST")

    try:
        # Test that BrowserConfig accepts the new parameters
        config = BrowserConfig(
            cdp_url="http://localhost:9222",
            browser_context_id="test-context-id",
            target_id="test-target-id",
            headless=True
        )

        # Verify parameters are set correctly
        assert config.browser_context_id == "test-context-id", "browser_context_id not set"
        assert config.target_id == "test-target-id", "target_id not set"

        # Test from_kwargs
        config2 = BrowserConfig.from_kwargs({
            "cdp_url": "http://localhost:9222",
            "browser_context_id": "test-context-id-2",
            "target_id": "test-target-id-2"
        })

        assert config2.browser_context_id == "test-context-id-2", "browser_context_id not set via from_kwargs"
        assert config2.target_id == "test-target-id-2", "target_id not set via from_kwargs"

        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict.get("browser_context_id") == "test-context-id", "browser_context_id not in to_dict"
        assert config_dict.get("target_id") == "test-target-id", "target_id not in to_dict"

        logger.success("BrowserConfig browser_context_id test passed", tag="TEST")
        return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        return False