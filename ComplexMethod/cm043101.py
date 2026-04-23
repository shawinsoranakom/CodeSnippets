async def demo_performance_analysis():
    """Using network capture for performance analysis"""
    print("\n=== 6. Performance Analysis with Network Capture ===")

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            capture_network_requests=True,
            page_timeout=60 * 2 * 1000  # 120 seconds
        )

        result = await crawler.arun(
            url="https://www.cnn.com/",
            config=config
        )

        if result.success and result.network_requests:
            # Filter only response events with timing information
            responses_with_timing = [
                r for r in result.network_requests 
                if r.get("event_type") == "response" and r.get("request_timing")
            ]

            if responses_with_timing:
                print(f"Analyzing timing for {len(responses_with_timing)} network responses")

                # Group by resource type
                resource_timings = {}
                for resp in responses_with_timing:
                    url = resp.get("url", "")
                    timing = resp.get("request_timing", {})

                    # Determine resource type from URL extension
                    ext = url.split(".")[-1].lower() if "." in url.split("/")[-1] else "unknown"
                    if ext in ["jpg", "jpeg", "png", "gif", "webp", "svg", "ico"]:
                        resource_type = "image"
                    elif ext in ["js"]:
                        resource_type = "javascript"
                    elif ext in ["css"]:
                        resource_type = "css"
                    elif ext in ["woff", "woff2", "ttf", "otf", "eot"]:
                        resource_type = "font"
                    else:
                        resource_type = "other"

                    if resource_type not in resource_timings:
                        resource_timings[resource_type] = []

                    # Calculate request duration if timing information is available
                    if isinstance(timing, dict) and "requestTime" in timing and "receiveHeadersEnd" in timing:
                        # Convert to milliseconds
                        duration = (timing["receiveHeadersEnd"] - timing["requestTime"]) * 1000
                        resource_timings[resource_type].append({
                            "url": url,
                            "duration_ms": duration
                        })
                    if isinstance(timing, dict) and "requestStart" in timing and "responseStart" in timing and "startTime" in timing:
                        # Convert to milliseconds
                        duration = (timing["responseStart"] - timing["requestStart"]) * 1000
                        resource_timings[resource_type].append({
                            "url": url,
                            "duration_ms": duration
                        })

                # Calculate statistics for each resource type
                print("\nPerformance by resource type:")
                for resource_type, timings in resource_timings.items():
                    if timings:
                        durations = [t["duration_ms"] for t in timings]
                        avg_duration = sum(durations) / len(durations)
                        max_duration = max(durations)
                        slowest_resource = next(t["url"] for t in timings if t["duration_ms"] == max_duration)

                        print(f"  {resource_type.upper()}:")
                        print(f"    - Count: {len(timings)}")
                        print(f"    - Avg time: {avg_duration:.2f} ms")
                        print(f"    - Max time: {max_duration:.2f} ms")
                        print(f"    - Slowest: {slowest_resource}")

                # Identify the slowest resources overall
                all_timings = []
                for resource_type, timings in resource_timings.items():
                    for timing in timings:
                        timing["type"] = resource_type
                        all_timings.append(timing)

                all_timings.sort(key=lambda x: x["duration_ms"], reverse=True)

                print("\nTop 5 slowest resources:")
                for i, timing in enumerate(all_timings[:5], 1):
                    print(f"  {i}. [{timing['type']}] {timing['url']} - {timing['duration_ms']:.2f} ms")

                # Save performance analysis to file
                output_file = os.path.join(__cur_dir__, "tmp", "performance_analysis.json")
                with open(output_file, "w") as f:
                    json.dump({
                        "url": result.url,
                        "timestamp": datetime.now().isoformat(),
                        "resource_timings": resource_timings,
                        "slowest_resources": all_timings[:10]  # Save top 10
                    }, f, indent=2)

                print(f"\nFull performance analysis saved to {output_file}")