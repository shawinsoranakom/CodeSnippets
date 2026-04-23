async def do_crawl(i):
        nonlocal completed, errors
        async with sem:
            try:
                crawl_config = CrawlerRunConfig(magic=True, cache_mode="bypass")
                page, ctx = await asyncio.wait_for(
                    bm.get_page(crawl_config),
                    timeout=30.0
                )

                try:
                    await page.goto("https://example.com", timeout=15000)
                except Exception:
                    pass

                # Use the FIXED finally pattern: release first, then close
                try:
                    await bm.release_page_with_context(page)
                except Exception:
                    pass
                try:
                    await page.close()
                except Exception:
                    pass

                completed += 1
                if completed % 20 == 0:
                    print(f"  [{completed}/{TOTAL}] version={bm._browser_version} "
                          f"pending={len(bm._pending_cleanup)} "
                          f"pages_served={bm._pages_served}")

            except asyncio.TimeoutError:
                errors += 1
                print(f"  [{i}] TIMEOUT in get_page()!")
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  [{i}] Error: {e}")