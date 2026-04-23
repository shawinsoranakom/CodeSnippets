async def basic_link_head_extraction():
    """
    Basic example: Extract head content from internal links with scoring
    """
    print("🔗 Basic Link Head Extraction Example")
    print("=" * 50)

    config = CrawlerRunConfig(
        # Enable link head extraction
        link_preview_config=LinkPreviewConfig(
            include_internal=True,           # Process internal links
            include_external=False,          # Skip external links for this demo
            max_links=5,                    # Limit to 5 links
            concurrency=3,                  # Process 3 links simultaneously
            timeout=10,                     # 10 second timeout per link
            query="API documentation guide", # Query for relevance scoring
            verbose=True                    # Show detailed progress
        ),
        # Enable intrinsic link scoring
        score_links=True,
        only_text=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://docs.python.org/3/", config=config)

        if result.success:
            print(f"\n✅ Successfully crawled: {result.url}")

            internal_links = result.links.get("internal", [])
            links_with_head = [link for link in internal_links 
                             if link.get("head_data") is not None]

            print(f"🧠 Links with head data: {len(links_with_head)}")

            # Show detailed results
            for i, link in enumerate(links_with_head[:3]):
                print(f"\n📄 Link {i+1}: {link['href']}")
                print(f"   Text: '{link.get('text', 'No text')[:50]}...'")

                # Show all three score types
                intrinsic = link.get('intrinsic_score')
                contextual = link.get('contextual_score') 
                total = link.get('total_score')

                print(f"   📊 Scores:")
                if intrinsic is not None:
                    print(f"      • Intrinsic: {intrinsic:.2f}/10.0")
                if contextual is not None:
                    print(f"      • Contextual: {contextual:.3f}")
                if total is not None:
                    print(f"      • Total: {total:.3f}")

                # Show head data
                head_data = link.get("head_data", {})
                if head_data:
                    title = head_data.get("title", "No title")
                    description = head_data.get("meta", {}).get("description", "")
                    print(f"   📰 Title: {title[:60]}...")
                    if description:
                        print(f"   📝 Description: {description[:80]}...")
        else:
            print(f"❌ Crawl failed: {result.error_message}")