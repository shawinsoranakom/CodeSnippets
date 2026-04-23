def example_1_string_based_hooks():
    """
    Demonstrate string-based hooks with REST API
    Use this when working with REST API directly or non-Python clients
    """
    print_section(
        "APPROACH 1: String-Based Hooks (REST API)",
        "Define hooks as strings for REST API requests"
    )

    # Define hooks as strings
    hooks_config = {
        "on_page_context_created": """
async def hook(page, context, **kwargs):
    print("  [String Hook] Setting up page context...")
    # Block images for performance
    await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
    await page.set_viewport_size({"width": 1920, "height": 1080})
    return page
""",

        "before_goto": """
async def hook(page, context, url, **kwargs):
    print(f"  [String Hook] Navigating to {url[:50]}...")
    await page.set_extra_http_headers({
        'X-Crawl4AI': 'string-based-hooks',
    })
    return page
""",

        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    print("  [String Hook] Scrolling page...")
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)
    return page
"""
    }

    # Prepare request payload
    payload = {
        "urls": [TEST_URLS[2]],  # httpbin.org
        "hooks": {
            "code": hooks_config,
            "timeout": 30
        },
        "crawler_config": {
            "cache_mode": "bypass"
        }
    }

    print(f"🎯 Target URL: {TEST_URLS[2]}")
    print(f"🔧 Configured {len(hooks_config)} string-based hooks")
    print(f"📡 Sending request to Docker API...\n")

    try:
        start_time = time.time()
        response = requests.post(f"{DOCKER_URL}/crawl", json=payload, timeout=60)
        execution_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()

            print(f"\n✅ Request successful! (took {execution_time:.2f}s)")

            # Display results
            if result.get('results') and result['results'][0].get('success'):
                crawl_result = result['results'][0]
                html_length = len(crawl_result.get('html', ''))
                markdown_length = len(crawl_result.get('markdown', ''))

                print(f"\n📊 Results:")
                print(f"   • HTML length: {html_length:,} characters")
                print(f"   • Markdown length: {markdown_length:,} characters")
                print(f"   • URL: {crawl_result.get('url')}")

                # Check hooks execution
                if 'hooks' in result:
                    hooks_info = result['hooks']
                    print(f"\n🎣 Hooks Execution:")
                    print(f"   • Status: {hooks_info['status']['status']}")
                    print(f"   • Attached hooks: {len(hooks_info['status']['attached_hooks'])}")

                    if 'summary' in hooks_info:
                        summary = hooks_info['summary']
                        print(f"   • Total executions: {summary['total_executions']}")
                        print(f"   • Successful: {summary['successful']}")
                        print(f"   • Success rate: {summary['success_rate']:.1f}%")
            else:
                print(f"⚠️ Crawl completed but no results")

        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Error: {response.text[:200]}")

    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 60 seconds")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    print("\n" + "─" * 70)
    print("✓ String-based hooks example complete\n")