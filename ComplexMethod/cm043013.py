async def test_memory_saving_flags_applied(test_server):
    """Verify --aggressive-cache-discard and --js-flags are in the launch args
    when memory_saving_mode=True, and absent when False."""
    config_on = BrowserConfig(
        headless=True,
        verbose=False,
        memory_saving_mode=True,
    )
    config_off = BrowserConfig(
        headless=True,
        verbose=False,
        memory_saving_mode=False,
    )

    async with AsyncWebCrawler(config=config_on) as crawler:
        bm = _bm(crawler)
        browser_args = bm._build_browser_args()
        # _build_browser_args returns a dict with an "args" key
        args_list = browser_args.get("args", browser_args) if isinstance(browser_args, dict) else browser_args
        assert "--aggressive-cache-discard" in args_list, (
            "memory_saving_mode=True should add --aggressive-cache-discard"
        )
        assert any("max-old-space-size" in a for a in args_list), (
            "memory_saving_mode=True should add V8 heap cap"
        )
        # Always-on flags should be present regardless
        assert any("OptimizationHints" in a for a in args_list)

    async with AsyncWebCrawler(config=config_off) as crawler:
        bm = _bm(crawler)
        browser_args = bm._build_browser_args()
        args_list = browser_args.get("args", browser_args) if isinstance(browser_args, dict) else browser_args
        assert "--aggressive-cache-discard" not in args_list, (
            "memory_saving_mode=False should NOT add --aggressive-cache-discard"
        )
        assert not any("max-old-space-size" in a for a in args_list), (
            "memory_saving_mode=False should NOT add V8 heap cap"
        )
        # Always-on flags should still be there
        assert any("OptimizationHints" in a for a in args_list)