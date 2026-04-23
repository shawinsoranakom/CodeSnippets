async def demo_1_docker_hooks_system():
    """Demo 1: Docker Hooks System - Real API calls with custom hooks"""
    print_section(
        "Demo 1: Docker Hooks System",
        "Testing both string-based and function-based hooks (NEW in v0.7.5!)"
    )

    # Check Docker service availability
    def check_docker_service():
        try:
            response = requests.get("http://localhost:11235/", timeout=3)
            return response.status_code == 200
        except:
            return False

    print("Checking Docker service...")
    docker_running = check_docker_service()

    if not docker_running:
        print("⚠️  Docker service not running on localhost:11235")
        print("To test Docker hooks:")
        print("1. Run: docker run -p 11235:11235 unclecode/crawl4ai:latest")
        print("2. Wait for service to start")
        print("3. Re-run this demo\n")
        return

    print("✓ Docker service detected!")

    # ============================================================================
    # PART 1: Traditional String-Based Hooks (Works with REST API)
    # ============================================================================
    print("\n" + "─" * 60)
    print("Part 1: String-Based Hooks (REST API)")
    print("─" * 60)

    hooks_config_string = {
        "on_page_context_created": """
async def hook(page, context, **kwargs):
    print("[String Hook] Setting up page context")
    await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
    return page
""",
        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    print("[String Hook] Before retrieving HTML")
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)
    return page
"""
    }

    payload = {
        "urls": ["https://httpbin.org/html"],
        "hooks": {
            "code": hooks_config_string,
            "timeout": 30
        }
    }

    print("🔧 Using string-based hooks for REST API...")
    try:
        start_time = time.time()
        response = requests.post("http://localhost:11235/crawl", json=payload, timeout=60)
        execution_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            print(f"✅ String-based hooks executed in {execution_time:.2f}s")
            if result.get('results') and result['results'][0].get('success'):
                html_length = len(result['results'][0].get('html', ''))
                print(f"   📄 HTML length: {html_length} characters")
        else:
            print(f"❌ Request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    # ============================================================================
    # PART 2: NEW Function-Based Hooks with Docker Client (v0.7.5)
    # ============================================================================
    print("\n" + "─" * 60)
    print("Part 2: Function-Based Hooks with Docker Client (✨ NEW!)")
    print("─" * 60)

    # Define hooks as regular Python functions
    async def on_page_context_created_func(page, context, **kwargs):
        """Block images to speed up crawling"""
        print("[Function Hook] Setting up page context")
        await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
        await page.set_viewport_size({"width": 1920, "height": 1080})
        return page

    async def before_goto_func(page, context, url, **kwargs):
        """Add custom headers before navigation"""
        print(f"[Function Hook] About to navigate to {url}")
        await page.set_extra_http_headers({
            'X-Crawl4AI': 'v0.7.5-function-hooks',
            'X-Test-Header': 'demo'
        })
        return page

    async def before_retrieve_html_func(page, context, **kwargs):
        """Scroll to load lazy content"""
        print("[Function Hook] Scrolling page for lazy-loaded content")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(500)
        await page.evaluate("window.scrollTo(0, 0)")
        return page

    # Use the hooks_to_string utility (can be used standalone)
    print("\n📦 Converting functions to strings with hooks_to_string()...")
    hooks_as_strings = hooks_to_string({
        "on_page_context_created": on_page_context_created_func,
        "before_goto": before_goto_func,
        "before_retrieve_html": before_retrieve_html_func
    })
    print(f"   ✓ Converted {len(hooks_as_strings)} hooks to string format")

    # OR use Docker Client which does conversion automatically!
    print("\n🐳 Using Docker Client with automatic conversion...")
    try:
        client = Crawl4aiDockerClient(base_url="http://localhost:11235")

        # Pass function objects directly - conversion happens automatically!
        results = await client.crawl(
            urls=["https://httpbin.org/html"],
            hooks={
                "on_page_context_created": on_page_context_created_func,
                "before_goto": before_goto_func,
                "before_retrieve_html": before_retrieve_html_func
            },
            hooks_timeout=30
        )

        if results and results.success:
            print(f"✅ Function-based hooks executed successfully!")
            print(f"   📄 HTML length: {len(results.html)} characters")
            print(f"   🎯 URL: {results.url}")
        else:
            print("⚠️ Crawl completed but may have warnings")

    except Exception as e:
        print(f"❌ Docker client error: {str(e)}")

    # Show the benefits
    print("\n" + "=" * 60)
    print("✨ Benefits of Function-Based Hooks:")
    print("=" * 60)
    print("✓ Full IDE support (autocomplete, syntax highlighting)")
    print("✓ Type checking and linting")
    print("✓ Easier to test and debug")
    print("✓ Reusable across projects")
    print("✓ Automatic conversion in Docker client")
    print("=" * 60)