async def test_link_extractor():
    """Test the link extractor functionality"""

    print("🔗 Testing Link Extractor Functionality")
    print("=" * 50)

    # Test configuration with link extraction AND scoring enabled
    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            include_external=False,  # Only internal links for this test
            # No include/exclude patterns for first test - let's see what we get
            query="API documentation reference guide",
            score_threshold=0.3,
            concurrency=5,
            timeout=10,
            max_links=5,  # Just test with 5 links first
            verbose=True  # Show detailed progress
        ),
        score_links=True,  # Enable intrinsic link scoring
        only_text=True,
        verbose=True
    )

    # Test URLs
    test_urls = [
        "https://docs.python.org/3/",  # Python docs - should have many internal links
        "https://httpbin.org/",        # Simple site for testing
    ]

    async with AsyncWebCrawler() as crawler:
        for url in test_urls:
            print(f"\n🌐 Testing URL: {url}")
            print("-" * 40)

            try:
                result = await crawler.arun(url, config=config)

                # Debug: Check if link extraction config is being passed
                print(f"🔍 Debug - Link extraction config: {config.link_preview_config.to_dict() if config.link_preview_config else None}")
                print(f"🔍 Debug - Score links: {config.score_links}")

                if result.success:
                    print(f"✅ Crawl successful!")
                    print(
                        f"📄 Page title: {result.metadata.get('title', 'No title')}")

                    # Check links - handle both dict and Links object structure
                    if isinstance(result.links, dict):
                        internal_links = [
                            Link(**link) for link in result.links.get('internal', [])]
                        external_links = [
                            Link(**link) for link in result.links.get('external', [])]
                    else:
                        internal_links = result.links.internal
                        external_links = result.links.external

                    print(f"🔗 Found {len(internal_links)} internal links")
                    print(f"🌍 Found {len(external_links)} external links")

                    # Show links with head data
                    links_with_head = [link for link in internal_links + external_links
                                       if hasattr(link, 'head_data') and link.head_data]

                    print(
                        f"🧠 Links with head data extracted: {len(links_with_head)}")

                    # Show all score types for all links (first 3)
                    all_links = internal_links + external_links
                    if all_links:
                        print(f"\n🔢 Sample link scores (first 3 links):")
                        for i, link in enumerate(all_links[:3]):
                            print(f"\n  {i+1}. {link.href}")

                            # Show intrinsic score
                            if hasattr(link, 'intrinsic_score') and link.intrinsic_score is not None:
                                if link.intrinsic_score == float('inf'):
                                    print(f"     Intrinsic Score: ∞ (scoring disabled)")
                                else:
                                    print(f"     Intrinsic Score: {link.intrinsic_score:.2f}/10.0")
                            else:
                                print(f"     Intrinsic Score: Not available")

                            # Show contextual score (BM25)
                            if hasattr(link, 'contextual_score') and link.contextual_score is not None:
                                print(f"     Contextual Score: {link.contextual_score:.3f}")
                            else:
                                print(f"     Contextual Score: Not available")

                            # Show total score
                            if hasattr(link, 'total_score') and link.total_score is not None:
                                print(f"     Total Score: {link.total_score:.3f}")
                            else:
                                print(f"     Total Score: Not available")

                            print(f"     Text: '{link.text[:50]}...' " if link.text else "     Text: (no text)")

                    if links_with_head:
                        print("\n📊 Sample links with head data:")
                        # Show top 3
                        for i, link in enumerate(links_with_head[:3]):
                            print(f"\n  {i+1}. {link.href}")
                            print(
                                f"     Status: {link.head_extraction_status}")

                            # Show all three score types
                            print(f"     📊 Scoring Summary:")
                            if hasattr(link, 'intrinsic_score') and link.intrinsic_score is not None:
                                if link.intrinsic_score == float('inf'):
                                    print(f"       • Intrinsic Score: ∞ (scoring disabled)")
                                else:
                                    print(f"       • Intrinsic Score: {link.intrinsic_score:.2f}/10.0")
                            else:
                                print(f"       • Intrinsic Score: Not available")

                            if hasattr(link, 'contextual_score') and link.contextual_score is not None:
                                print(f"       • Contextual Score: {link.contextual_score:.3f}")
                            else:
                                print(f"       • Contextual Score: Not available")

                            if hasattr(link, 'total_score') and link.total_score is not None:
                                print(f"       • Total Score: {link.total_score:.3f}")
                            else:
                                print(f"       • Total Score: Not available")

                            if link.head_data:
                                title = link.head_data.get('title', 'No title')
                                if title:
                                    print(f"     Title: {title[:60]}...")

                                meta = link.head_data.get('meta', {})
                                if 'description' in meta and meta['description']:
                                    desc = meta['description']
                                    print(f"     Description: {desc[:80]}...")

                                # Show link metadata keys (should now be properly formatted)
                                link_data = link.head_data.get('link', {})
                                if link_data:
                                    keys = list(link_data.keys())[:3]
                                    print(f"     Link types: {keys}")

                    # Show failed extractions
                    failed_links = [link for link in internal_links + external_links
                                    if hasattr(link, 'head_extraction_status') and
                                    link.head_extraction_status == 'failed']

                    if failed_links:
                        print(
                            f"\n❌ Failed head extractions: {len(failed_links)}")
                        for link in failed_links[:2]:  # Show first 2 failures
                            print(f"  - {link.href}")
                            if hasattr(link, 'head_extraction_error') and link.head_extraction_error:
                                print(
                                    f"    Error: {link.head_extraction_error}")

                else:
                    print(f"❌ Crawl failed: {result.error_message}")

            except Exception as e:
                print(f"💥 Error testing {url}: {str(e)}")
                import traceback
                traceback.print_exc()