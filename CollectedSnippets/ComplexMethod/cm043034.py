async def test_isolated_context(cdp_url: str = None, attempts: int = 3):
    """Test with isolated context (works with both Playwright and CDP)."""
    mode = f"CDP ({cdp_url})" if cdp_url else "Playwright Chromium"
    print(f"\n{'='*60}")
    print(f"Mode: Isolated context — {mode}")
    print(f"{'='*60}\n")

    kwargs = dict(
        enable_stealth=True,
        create_isolated_context=True,
        viewport_width=1920,
        viewport_height=1080,
    )
    if cdp_url:
        kwargs["cdp_url"] = cdp_url
    else:
        kwargs["headless"] = True

    config = BrowserConfig(**kwargs)
    run_config = CrawlerRunConfig(
        magic=True,
        simulate_user=True,
        override_navigator=True,
        proxy_config=get_proxy_config(),
        page_timeout=120000,
        wait_until="load",
        delay_before_return_html=15.0,
    )

    passed = 0
    async with AsyncWebCrawler(config=config) as crawler:
        for i in range(attempts):
            result = await crawler.arun(URL, config=run_config)
            ok = result.status_code == 200 and len(result.html) > 10000
            title = ""
            if ok:
                passed += 1
                m = re.search(r"<title>(.*?)</title>", result.html)
                title = f"  title={m.group(1)}" if m else ""
            print(f"  Attempt {i+1}: status={result.status_code}  html={len(result.html):>10,} bytes  {'PASS' if ok else 'FAIL'}{title}")

    print(f"\nResult: {passed}/{attempts} passed")
    return passed > 0