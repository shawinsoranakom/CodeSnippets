async def analyze_spa_network_traffic():
    """Analyze network traffic of a Single-Page Application"""
    print("\n=== 4. Analyzing SPA Network Traffic ===")

    async with AsyncWebCrawler(config=BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800
    )) as crawler:
        config = CrawlerRunConfig(
            capture_network_requests=True,
            capture_console_messages=True,
            # Wait longer to ensure all resources are loaded
            wait_until="networkidle",
            page_timeout=60000,  # 60 seconds
        )

        result = await crawler.arun(
            url="https://weather.com",
            config=config
        )

        if result.success and result.network_requests:
            # Extract different types of requests
            requests = []
            responses = []
            failures = []

            for event in result.network_requests:
                event_type = event.get("event_type")
                if event_type == "request":
                    requests.append(event)
                elif event_type == "response":
                    responses.append(event)
                elif event_type == "request_failed":
                    failures.append(event)

            print(f"Captured {len(requests)} requests, {len(responses)} responses, and {len(failures)} failures")

            # Analyze request types
            resource_types = {}
            for req in requests:
                resource_type = req.get("resource_type", "unknown")
                resource_types[resource_type] = resource_types.get(resource_type, 0) + 1

            print("\nResource types:")
            for resource_type, count in sorted(resource_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {resource_type}: {count}")

            # Analyze API calls
            api_calls = [r for r in requests if "api" in r.get("url", "").lower()]
            if api_calls:
                print(f"\nDetected {len(api_calls)} API calls:")
                for i, call in enumerate(api_calls[:5], 1):  # Show first 5
                    print(f"  {i}. {call.get('method')} {call.get('url')}")
                if len(api_calls) > 5:
                    print(f"     ... and {len(api_calls) - 5} more")

            # Analyze response status codes
            status_codes = {}
            for resp in responses:
                status = resp.get("status", 0)
                status_codes[status] = status_codes.get(status, 0) + 1

            print("\nResponse status codes:")
            for status, count in sorted(status_codes.items()):
                print(f"  - {status}: {count}")

            # Analyze failures
            if failures:
                print("\nFailed requests:")
                for i, failure in enumerate(failures[:5], 1):  # Show first 5
                    print(f"  {i}. {failure.get('url')} - {failure.get('failure_text')}")
                if len(failures) > 5:
                    print(f"     ... and {len(failures) - 5} more")

            # Check for console errors
            if result.console_messages:
                errors = [msg for msg in result.console_messages if msg.get("type") == "error"]
                if errors:
                    print(f"\nDetected {len(errors)} console errors:")
                    for i, error in enumerate(errors[:3], 1):  # Show first 3
                        print(f"  {i}. {error.get('text', '')[:100]}...")
                    if len(errors) > 3:
                        print(f"     ... and {len(errors) - 3} more")

            # Save analysis to file
            output_file = os.path.join(__cur_dir__, "tmp", "weather_network_analysis.json")
            with open(output_file, "w") as f:
                json.dump({
                    "url": result.url,
                    "timestamp": datetime.now().isoformat(),
                    "statistics": {
                        "request_count": len(requests),
                        "response_count": len(responses),
                        "failure_count": len(failures),
                        "resource_types": resource_types,
                        "status_codes": {str(k): v for k, v in status_codes.items()},
                        "api_call_count": len(api_calls),
                        "console_error_count": len(errors) if result.console_messages else 0
                    },
                    "network_requests": result.network_requests,
                    "console_messages": result.console_messages
                }, f, indent=2)

            print(f"\nFull analysis saved to {output_file}")