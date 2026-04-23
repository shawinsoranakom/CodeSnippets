def test_basic_crawl_with_hooks():
    """Test basic crawling with user-provided hooks"""
    print("\n" + "=" * 70)
    print("Testing: POST /crawl with hooks")
    print("=" * 70)

    # Define hooks as Python code strings
    hooks_code = {
        "on_page_context_created": """
async def hook(page, context, **kwargs):
    print("Hook: Setting up page context")
    # Block images to speed up crawling
    await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
    print("Hook: Images blocked")
    return page
""",

        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    print("Hook: Before retrieving HTML")
    # Scroll to bottom to load lazy content
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)
    print("Hook: Scrolled to bottom")
    return page
""",

        "before_goto": """
async def hook(page, context, url, **kwargs):
    print(f"Hook: About to navigate to {url}")
    # Add custom headers
    await page.set_extra_http_headers({
        'X-Test-Header': 'crawl4ai-hooks-test'
    })
    return page
"""
    }

    # Create request payload
    payload = {
        "urls": ["https://httpbin.org/html"],
        "hooks": {
            "code": hooks_code,
            "timeout": 30
        }
    }

    print("Sending request with hooks...")
    response = requests.post(f"{API_BASE_URL}/crawl", json=payload)

    if response.status_code == 200:
        data = response.json()
        print("\n✅ Crawl successful!")

        # Check hooks status
        if 'hooks' in data:
            hooks_info = data['hooks']
            print("\nHooks Execution Summary:")
            print(f"  Status: {hooks_info['status']['status']}")
            print(f"  Attached hooks: {', '.join(hooks_info['status']['attached_hooks'])}")

            if hooks_info['status']['validation_errors']:
                print("\n⚠️ Validation Errors:")
                for error in hooks_info['status']['validation_errors']:
                    print(f"  - {error['hook_point']}: {error['error']}")

            if 'summary' in hooks_info:
                summary = hooks_info['summary']
                print(f"\nExecution Statistics:")
                print(f"  Total executions: {summary['total_executions']}")
                print(f"  Successful: {summary['successful']}")
                print(f"  Failed: {summary['failed']}")
                print(f"  Timed out: {summary['timed_out']}")
                print(f"  Success rate: {summary['success_rate']:.1f}%")

            if hooks_info['execution_log']:
                print("\nExecution Log:")
                for log_entry in hooks_info['execution_log']:
                    status_icon = "✅" if log_entry['status'] == 'success' else "❌"
                    print(f"  {status_icon} {log_entry['hook_point']}: {log_entry['status']} ({log_entry.get('execution_time', 0):.2f}s)")

            if hooks_info['errors']:
                print("\n❌ Hook Errors:")
                for error in hooks_info['errors']:
                    print(f"  - {error['hook_point']}: {error['error']}")

        # Show crawl results
        if 'results' in data:
            print(f"\nCrawled {len(data['results'])} URL(s)")
            for result in data['results']:
                print(f"  - {result['url']}: {'✅' if result['success'] else '❌'}")

    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)