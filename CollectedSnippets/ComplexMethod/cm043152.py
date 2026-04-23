async def demo_2_request_tracking():
    """Demo 2: Real-time Request Tracking - Generate and monitor requests"""
    print_section(
        "Demo 2: Real-time Request Tracking",
        "Submit crawl jobs and watch them in real-time"
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        print("🚀 Submitting crawl requests...")

        # Submit multiple requests
        urls_to_crawl = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://example.com"
        ]

        tasks = []
        for url in urls_to_crawl:
            task = client.post(
                f"{CRAWL4AI_BASE_URL}/crawl",
                json={"urls": [url], "crawler_config": {}}
            )
            tasks.append(task)

        print(f"   • Submitting {len(urls_to_crawl)} requests in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 200)
        print(f"   ✅ {successful}/{len(urls_to_crawl)} requests submitted")

        # Check request tracking
        print("\n📊 Checking request tracking...")
        await asyncio.sleep(2)  # Wait for requests to process

        response = await client.get(f"{CRAWL4AI_BASE_URL}/monitor/requests")
        requests_data = response.json()

        print(f"\n📋 Request Status:")
        print(f"   • Active Requests: {len(requests_data['active'])}")
        print(f"   • Completed Requests: {len(requests_data['completed'])}")

        if requests_data['completed']:
            print(f"\n📝 Recent Completed Requests:")
            for req in requests_data['completed'][:3]:
                status_icon = "✅" if req['success'] else "❌"
                print(f"   {status_icon} {req['endpoint']} - {req['latency_ms']:.0f}ms")