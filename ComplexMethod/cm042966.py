async def test_multiple_crawlers_same_cdp():
    """
    Test 8: Multiple AsyncWebCrawler instances connecting to the same CDP endpoint.

    This tests the realistic scenario where:
    1. A browser is started externally (or by a managed browser)
    2. Multiple crawler instances connect to it via CDP URL
    3. All use create_isolated_context=False to share cookies/session
    4. Each should get its own page to avoid race conditions
    """
    print("\n" + "="*70)
    print("TEST 8: Multiple crawlers connecting to same CDP endpoint")
    print("="*70)

    import subprocess
    import tempfile

    # Start a browser manually using subprocess
    port = 9444
    temp_dir = tempfile.mkdtemp(prefix="browser-test-")

    browser_process = None
    try:
        # Start chromium with remote debugging - use Playwright's bundled chromium
        import os
        playwright_path = os.path.expanduser("~/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome")
        if not os.path.exists(playwright_path):
            # Fallback - try to find it
            for path in [
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/usr/bin/google-chrome",
            ]:
                if os.path.exists(path):
                    playwright_path = path
                    break
        chrome_path = playwright_path

        cmd = [
            chrome_path,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={temp_dir}",
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
        ]

        browser_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await asyncio.sleep(2)  # Wait for browser to start

        cdp_url = f"http://localhost:{port}"
        print(f"  Started browser at {cdp_url}")

        # Both crawlers connect via CDP URL
        browser_config1 = BrowserConfig(
            headless=True,
            cdp_url=cdp_url,
            create_isolated_context=False,
        )
        browser_config2 = BrowserConfig(
            headless=True,
            cdp_url=cdp_url,
            create_isolated_context=False,
        )

        urls_crawler1 = [
            "https://example.com?crawler=1",
            "https://example.org?crawler=1",
        ]
        urls_crawler2 = [
            "https://httpbin.org/html?crawler=2",
            "https://httpbin.org/get?crawler=2",
        ]

        async with AsyncWebCrawler(config=browser_config1) as crawler1:
            async with AsyncWebCrawler(config=browser_config2) as crawler2:
                bm1 = crawler1.crawler_strategy.browser_manager
                bm2 = crawler2.crawler_strategy.browser_manager

                print(f"  Crawler 1 endpoint key: {bm1._browser_endpoint_key}")
                print(f"  Crawler 2 endpoint key: {bm2._browser_endpoint_key}")
                print(f"  Keys match: {bm1._browser_endpoint_key == bm2._browser_endpoint_key}")

                # Launch concurrent crawls from BOTH crawlers simultaneously
                print(f"  Launching {len(urls_crawler1) + len(urls_crawler2)} concurrent crawls...")

                tasks1 = [crawler1.arun(url) for url in urls_crawler1]
                tasks2 = [crawler2.arun(url) for url in urls_crawler2]

                all_results = await asyncio.gather(
                    *tasks1, *tasks2,
                    return_exceptions=True
                )

                # Check results
                success_count = 0
                for i, result in enumerate(all_results):
                    crawler_id = 1 if i < len(urls_crawler1) else 2
                    url_idx = i if i < len(urls_crawler1) else i - len(urls_crawler1)

                    if isinstance(result, Exception):
                        print(f"    Crawler {crawler_id}, URL {url_idx+1}: EXCEPTION - {result}")
                    elif result.success:
                        success_count += 1
                        print(f"    Crawler {crawler_id}, URL {url_idx+1}: OK")
                    else:
                        print(f"    Crawler {crawler_id}, URL {url_idx+1}: FAILED - {result.error_message}")

                total = len(urls_crawler1) + len(urls_crawler2)
                assert success_count == total, f"Only {success_count}/{total} succeeded"

                print(f"  PASSED: All {total} concurrent crawls from 2 crawlers succeeded")
                return True

    except Exception as e:
        print(f"  FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up browser process
        if browser_process:
            browser_process.terminate()
            try:
                browser_process.wait(timeout=5)
            except:
                browser_process.kill()
        # Clean up temp dir
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass