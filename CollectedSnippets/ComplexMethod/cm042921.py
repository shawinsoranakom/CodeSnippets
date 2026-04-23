def test_all_hooks_demo():
    """Demonstrate all 8 hook types with practical examples"""
    print("=" * 70)
    print("Testing: All Hooks Comprehensive Demo")
    print("=" * 70)

    hooks_code = {
        "on_browser_created": """
async def hook(browser, **kwargs):
    # Hook called after browser is created
    print("[HOOK] on_browser_created - Browser is ready!")
    # Browser-level configurations would go here
    return browser
""",

        "on_page_context_created": """
async def hook(page, context, **kwargs):
    # Hook called after a new page and context are created
    print("[HOOK] on_page_context_created - New page created!")

    # Set viewport size for consistent rendering
    await page.set_viewport_size({"width": 1920, "height": 1080})

    # Add cookies for the session (using httpbin.org domain)
    await context.add_cookies([
        {
            "name": "test_session",
            "value": "abc123xyz",
            "domain": ".httpbin.org",
            "path": "/",
            "httpOnly": True,
            "secure": True
        }
    ])

    # Block ads and tracking scripts to speed up crawling
    await context.route("**/*.{png,jpg,jpeg,gif,webp,svg}", lambda route: route.abort())
    await context.route("**/analytics/*", lambda route: route.abort())
    await context.route("**/ads/*", lambda route: route.abort())

    print("[HOOK] Viewport set, cookies added, and ads blocked")
    return page
""",

        "on_user_agent_updated": """
async def hook(page, context, user_agent, **kwargs):
    # Hook called when user agent is updated
    print(f"[HOOK] on_user_agent_updated - User agent: {user_agent[:50]}...")
    return page
""",

        "before_goto": """
async def hook(page, context, url, **kwargs):
    # Hook called before navigating to each URL
    print(f"[HOOK] before_goto - About to visit: {url}")

    # Add custom headers for the request
    await page.set_extra_http_headers({
        "X-Custom-Header": "crawl4ai-test",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1"
    })

    return page
""",

        "after_goto": """
async def hook(page, context, url, response, **kwargs):
    # Hook called after navigating to each URL
    print(f"[HOOK] after_goto - Successfully loaded: {url}")

    # Wait a moment for dynamic content to load
    await page.wait_for_timeout(1000)

    # Check if specific elements exist (with error handling)
    try:
        # For httpbin.org, wait for body element
        await page.wait_for_selector("body", timeout=2000)
        print("[HOOK] Body element found and loaded")
    except:
        print("[HOOK] Timeout waiting for body, continuing anyway")

    return page
""",

        "on_execution_started": """
async def hook(page, context, **kwargs):
    # Hook called after custom JavaScript execution
    print("[HOOK] on_execution_started - Custom JS executed!")

    # You could inject additional JavaScript here if needed
    await page.evaluate("console.log('[INJECTED] Hook JS running');")

    return page
""",

        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    # Hook called before retrieving the HTML content
    print("[HOOK] before_retrieve_html - Preparing to get HTML")

    # Scroll to bottom to trigger lazy loading
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
    await page.wait_for_timeout(500)

    # Scroll back to top
    await page.evaluate("window.scrollTo(0, 0);")
    await page.wait_for_timeout(500)

    # One more scroll to middle for good measure
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")

    print("[HOOK] Scrolling completed for lazy-loaded content")
    return page
""",

        "before_return_html": """
async def hook(page, context, html, **kwargs):
    # Hook called before returning the HTML content
    print(f"[HOOK] before_return_html - HTML length: {len(html)} characters")

    # Log some page metrics
    metrics = await page.evaluate('''() => {
        return {
            images: document.images.length,
            links: document.links.length,
            scripts: document.scripts.length
        }
    }''')

    print(f"[HOOK] Page metrics - Images: {metrics['images']}, Links: {metrics['links']}, Scripts: {metrics['scripts']}")

    return page
"""
    }

    # Create request payload
    payload = {
        "urls": ["https://httpbin.org/html"],
        "hooks": {
            "code": hooks_code,
            "timeout": 30
        },
        "crawler_config": {
            "js_code": "window.scrollTo(0, document.body.scrollHeight);",
            "wait_for": "body",
            "cache_mode": "bypass"
        }
    }

    print("\nSending request with all 8 hooks...")
    start_time = time.time()

    response = requests.post(f"{API_BASE_URL}/crawl", json=payload, headers=get_auth_headers())

    elapsed_time = time.time() - start_time
    print(f"Request completed in {elapsed_time:.2f} seconds")

    if response.status_code == 200:
        data = response.json()
        print("\n✅ Request successful!")

        # Check hooks execution
        if 'hooks' in data:
            hooks_info = data['hooks']
            print("\n📊 Hooks Execution Summary:")
            print(f"  Status: {hooks_info['status']['status']}")
            print(f"  Attached hooks: {len(hooks_info['status']['attached_hooks'])}")

            for hook_name in hooks_info['status']['attached_hooks']:
                print(f"    ✓ {hook_name}")

            if 'summary' in hooks_info:
                summary = hooks_info['summary']
                print(f"\n📈 Execution Statistics:")
                print(f"  Total executions: {summary['total_executions']}")
                print(f"  Successful: {summary['successful']}")
                print(f"  Failed: {summary['failed']}")
                print(f"  Timed out: {summary['timed_out']}")
                print(f"  Success rate: {summary['success_rate']:.1f}%")

            if hooks_info.get('execution_log'):
                print(f"\n📝 Execution Log:")
                for log_entry in hooks_info['execution_log']:
                    status_icon = "✅" if log_entry['status'] == 'success' else "❌"
                    exec_time = log_entry.get('execution_time', 0)
                    print(f"  {status_icon} {log_entry['hook_point']}: {exec_time:.3f}s")

        # Check crawl results
        if 'results' in data and len(data['results']) > 0:
            print(f"\n📄 Crawl Results:")
            for result in data['results']:
                print(f"  URL: {result['url']}")
                print(f"  Success: {result.get('success', False)}")
                if result.get('html'):
                    print(f"  HTML length: {len(result['html'])} characters")

    else:
        print(f"❌ Error: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Error text: {response.text[:500]}")