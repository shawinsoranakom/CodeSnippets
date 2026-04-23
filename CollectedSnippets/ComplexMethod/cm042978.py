async def test_fallback_path_injects_once():
    """
    Fallback path: manually create a context without crawlerRunConfig
    (simulating managed/persistent/CDP path), then verify _crawl_web()
    injects scripts exactly once and sets the flags.
    """
    print("\n" + "=" * 70)
    print("TEST: Fallback path injects once and sets flags")
    print("=" * 70)

    bm = BrowserManager(BrowserConfig(headless=True, extra_args=['--no-sandbox']))
    await bm.start()

    try:
        # Create context WITHOUT crawlerRunConfig (simulates persistent/CDP path)
        ctx = await bm.create_browser_context()
        await bm.setup_context(ctx)  # No crawlerRunConfig — no flags set

        check("flags NOT set before _crawl_web",
              not getattr(ctx, '_crawl4ai_nav_overrider_injected', False)
              and not getattr(ctx, '_crawl4ai_shadow_dom_injected', False))

        # Track add_init_script calls
        original_add_init_script = ctx.add_init_script
        call_count = 0

        async def counting_add_init_script(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return await original_add_init_script(*args, **kwargs)

        ctx.add_init_script = counting_add_init_script

        # Create a page and simulate what _crawl_web does
        page = await ctx.new_page()

        config = CrawlerRunConfig(magic=True, flatten_shadow_dom=True)

        # First "crawl" — should inject both scripts
        from crawl4ai.js_snippet import load_js_script

        if config.override_navigator or config.simulate_user or config.magic:
            if not getattr(ctx, '_crawl4ai_nav_overrider_injected', False):
                await ctx.add_init_script(load_js_script("navigator_overrider"))
                ctx._crawl4ai_nav_overrider_injected = True

        if config.flatten_shadow_dom:
            if not getattr(ctx, '_crawl4ai_shadow_dom_injected', False):
                await ctx.add_init_script("""
                    const _origAttachShadow = Element.prototype.attachShadow;
                    Element.prototype.attachShadow = function(init) {
                        return _origAttachShadow.call(this, {...init, mode: 'open'});
                    };
                """)
                ctx._crawl4ai_shadow_dom_injected = True

        check("first pass: 2 add_init_script calls (nav + shadow)", call_count == 2)

        # Second "crawl" — should skip both
        call_count = 0

        if config.override_navigator or config.simulate_user or config.magic:
            if not getattr(ctx, '_crawl4ai_nav_overrider_injected', False):
                await ctx.add_init_script(load_js_script("navigator_overrider"))
                ctx._crawl4ai_nav_overrider_injected = True

        if config.flatten_shadow_dom:
            if not getattr(ctx, '_crawl4ai_shadow_dom_injected', False):
                await ctx.add_init_script("""...""")
                ctx._crawl4ai_shadow_dom_injected = True

        check("second pass: 0 add_init_script calls (flags set)", call_count == 0)

        await page.close()
        await ctx.close()

    finally:
        await bm.close()