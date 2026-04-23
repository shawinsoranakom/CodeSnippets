async def demo_3_browser_pool_management():
    """Demo 3: Browser Pool Management - 3-tier architecture in action"""
    print_section(
        "Demo 3: Browser Pool Management",
        "Understanding permanent, hot, and cold browser pools"
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        print("🌊 Testing browser pool with different configurations...")

        # Test 1: Default config (permanent browser)
        print("\n🔥 Test 1: Default Config → Permanent Browser")
        for i in range(3):
            await client.post(
                f"{CRAWL4AI_BASE_URL}/crawl",
                json={"urls": [f"https://httpbin.org/html?req={i}"], "crawler_config": {}}
            )
            print(f"   • Request {i+1}/3 sent (should use permanent browser)")

        await asyncio.sleep(2)

        # Test 2: Custom viewport (cold → hot promotion after 3 uses)
        print("\n♨️  Test 2: Custom Viewport → Cold Pool (promoting to Hot)")
        viewport_config = {"viewport": {"width": 1280, "height": 720}}
        for i in range(4):
            await client.post(
                f"{CRAWL4AI_BASE_URL}/crawl",
                json={
                    "urls": [f"https://httpbin.org/json?viewport={i}"],
                    "browser_config": viewport_config,
                    "crawler_config": {}
                }
            )
            print(f"   • Request {i+1}/4 sent (cold→hot promotion after 3rd use)")

        await asyncio.sleep(2)

        # Check browser pool status
        print("\n📊 Browser Pool Report:")
        response = await client.get(f"{CRAWL4AI_BASE_URL}/monitor/browsers")
        browsers = response.json()

        print(f"\n🎯 Pool Summary:")
        print(f"   • Total Browsers: {browsers['summary']['total_count']}")
        print(f"   • Total Memory: {browsers['summary']['total_memory_mb']} MB")
        print(f"   • Reuse Rate: {browsers['summary']['reuse_rate_percent']:.1f}%")

        print(f"\n📋 Browser Pool Details:")
        if browsers['permanent']:
            for browser in browsers['permanent']:
                print(f"   🔥 Permanent: {browser['browser_id'][:8]}... | "
                      f"Requests: {browser['request_count']} | "
                      f"Memory: {browser['memory_mb']:.0f} MB")

        if browsers['hot']:
            for browser in browsers['hot']:
                print(f"   ♨️  Hot: {browser['browser_id'][:8]}... | "
                      f"Requests: {browser['request_count']} | "
                      f"Memory: {browser['memory_mb']:.0f} MB")

        if browsers['cold']:
            for browser in browsers['cold']:
                print(f"   ❄️  Cold: {browser['browser_id'][:8]}... | "
                      f"Requests: {browser['request_count']} | "
                      f"Memory: {browser['memory_mb']:.0f} MB")