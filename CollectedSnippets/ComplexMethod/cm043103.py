async def api_discovery_example():
    """
    API Discovery: Find API endpoints and references
    """
    print("\n\n🔧 API Discovery Example")
    print("=" * 50)

    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            include_patterns=["*/api/*", "*/reference/*", "*/endpoint/*"],
            exclude_patterns=["*/deprecated/*", "*/v1/*"],  # Skip old versions
            max_links=25,
            concurrency=10,
            timeout=8,
            verbose=False
        ),
        score_links=True
    )

    # Example with a documentation site that has API references
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://httpbin.org/", config=config)

        if result.success:
            print(f"✅ Discovered APIs at: {result.url}")

            api_links = result.links.get("internal", [])

            # Categorize by detected content
            endpoints = {"GET": [], "POST": [], "PUT": [], "DELETE": [], "OTHER": []}

            for link in api_links:
                if link.get("head_data"):
                    title = link.get("head_data", {}).get("title", "").upper()
                    text = link.get("text", "").upper()

                    # Simple categorization based on content
                    if "GET" in title or "GET" in text:
                        endpoints["GET"].append(link)
                    elif "POST" in title or "POST" in text:
                        endpoints["POST"].append(link)
                    elif "PUT" in title or "PUT" in text:
                        endpoints["PUT"].append(link)
                    elif "DELETE" in title or "DELETE" in text:
                        endpoints["DELETE"].append(link)
                    else:
                        endpoints["OTHER"].append(link)

            # Display results
            total_found = sum(len(links) for links in endpoints.values())
            print(f"\n📡 Found {total_found} API-related links:")

            for method, links in endpoints.items():
                if links:
                    print(f"\n{method} Endpoints ({len(links)}):")
                    for link in links[:3]:  # Show first 3 of each type
                        title = link.get("head_data", {}).get("title", "No title")
                        score = link.get("intrinsic_score", 0)
                        print(f"  • [{score:.1f}] {title[:50]}...")
                        print(f"    {link['href']}")
        else:
            print(f"❌ API discovery failed: {result.error_message}")