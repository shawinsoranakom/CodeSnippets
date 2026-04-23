async def test_configurable_backoff():
    """
    Verify LLMConfig accepts and stores backoff configuration parameters.

    BEFORE: Backoff was hardcoded (delay=2, attempts=3, factor=2)
    AFTER: LLMConfig accepts backoff_base_delay, backoff_max_attempts, backoff_exponential_factor
    """
    print_test("Configurable Backoff Parameters", "#1269")

    try:
        from crawl4ai import LLMConfig

        # Test 1: Default values
        default_config = LLMConfig(provider="openai/gpt-4o-mini")

        if default_config.backoff_base_delay != 2:
            record_result("Configurable Backoff", "#1269", False,
                         f"Default base_delay is {default_config.backoff_base_delay}, expected 2")
            return

        if default_config.backoff_max_attempts != 3:
            record_result("Configurable Backoff", "#1269", False,
                         f"Default max_attempts is {default_config.backoff_max_attempts}, expected 3")
            return

        if default_config.backoff_exponential_factor != 2:
            record_result("Configurable Backoff", "#1269", False,
                         f"Default exponential_factor is {default_config.backoff_exponential_factor}, expected 2")
            return

        # Test 2: Custom values
        custom_config = LLMConfig(
            provider="openai/gpt-4o-mini",
            backoff_base_delay=5,
            backoff_max_attempts=10,
            backoff_exponential_factor=3
        )

        if custom_config.backoff_base_delay != 5:
            record_result("Configurable Backoff", "#1269", False,
                         f"Custom base_delay is {custom_config.backoff_base_delay}, expected 5")
            return

        if custom_config.backoff_max_attempts != 10:
            record_result("Configurable Backoff", "#1269", False,
                         f"Custom max_attempts is {custom_config.backoff_max_attempts}, expected 10")
            return

        if custom_config.backoff_exponential_factor != 3:
            record_result("Configurable Backoff", "#1269", False,
                         f"Custom exponential_factor is {custom_config.backoff_exponential_factor}, expected 3")
            return

        # Test 3: to_dict() includes backoff params
        config_dict = custom_config.to_dict()
        if 'backoff_base_delay' not in config_dict:
            record_result("Configurable Backoff", "#1269", False,
                         "backoff_base_delay missing from to_dict()")
            return

        record_result("Configurable Backoff", "#1269", True,
                     "LLMConfig accepts and stores custom backoff parameters")

    except Exception as e:
        record_result("Configurable Backoff", "#1269", False, f"Exception: {e}")