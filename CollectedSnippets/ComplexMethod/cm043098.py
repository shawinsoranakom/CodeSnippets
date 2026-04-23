async def demo_basic_network_capture():
    """Basic network request capturing example"""
    print("\n=== 1. Basic Network Request Capturing ===")

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            capture_network_requests=True,
            wait_until="networkidle"  # Wait for network to be idle
        )

        result = await crawler.arun(
            url="https://example.com/",
            config=config
        )

        if result.success and result.network_requests:
            print(f"Captured {len(result.network_requests)} network events")

            # Count by event type
            event_types = {}
            for req in result.network_requests:
                event_type = req.get("event_type", "unknown")
                event_types[event_type] = event_types.get(event_type, 0) + 1

            print("Event types:")
            for event_type, count in event_types.items():
                print(f"  - {event_type}: {count}")

            # Show a sample request and response
            request = next((r for r in result.network_requests if r.get("event_type") == "request"), None)
            response = next((r for r in result.network_requests if r.get("event_type") == "response"), None)

            if request:
                print("\nSample request:")
                print(f"  URL: {request.get('url')}")
                print(f"  Method: {request.get('method')}")
                print(f"  Headers: {list(request.get('headers', {}).keys())}")

            if response:
                print("\nSample response:")
                print(f"  URL: {response.get('url')}")
                print(f"  Status: {response.get('status')} {response.get('status_text', '')}")
                print(f"  Headers: {list(response.get('headers', {}).keys())}")