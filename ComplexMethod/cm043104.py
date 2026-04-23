async def link_quality_analysis():
    """
    Link Quality Analysis: Analyze website structure and link quality
    """
    print("\n\n📊 Link Quality Analysis Example")
    print("=" * 50)

    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            max_links=30,  # Analyze more links for better statistics
            concurrency=15,
            timeout=6,
            verbose=False
        ),
        score_links=True
    )

    async with AsyncWebCrawler() as crawler:
        # Test with a content-rich site
        result = await crawler.arun("https://docs.python.org/3/", config=config)

        if result.success:
            print(f"✅ Analyzed: {result.url}")

            links = result.links.get("internal", [])

            # Extract intrinsic scores for analysis
            scores = [link.get('intrinsic_score', 0) for link in links if link.get('intrinsic_score') is not None]

            if scores:
                avg_score = sum(scores) / len(scores)
                high_quality = len([s for s in scores if s >= 7.0])
                medium_quality = len([s for s in scores if 4.0 <= s < 7.0])
                low_quality = len([s for s in scores if s < 4.0])

                print(f"\n📈 Quality Analysis Results:")
                print(f"   📊 Average Score: {avg_score:.2f}/10.0")
                print(f"   🟢 High Quality (≥7.0): {high_quality} links")
                print(f"   🟡 Medium Quality (4.0-6.9): {medium_quality} links")
                print(f"   🔴 Low Quality (<4.0): {low_quality} links")

                # Show best and worst links
                scored_links = [(link, link.get('intrinsic_score', 0)) for link in links 
                              if link.get('intrinsic_score') is not None]
                scored_links.sort(key=lambda x: x[1], reverse=True)

                print(f"\n🏆 Top 3 Quality Links:")
                for i, (link, score) in enumerate(scored_links[:3]):
                    text = link.get('text', 'No text')[:40]
                    print(f"   {i+1}. [{score:.1f}] {text}...")
                    print(f"      {link['href']}")

                print(f"\n⚠️  Bottom 3 Quality Links:")
                for i, (link, score) in enumerate(scored_links[-3:]):
                    text = link.get('text', 'No text')[:40]
                    print(f"   {i+1}. [{score:.1f}] {text}...")
                    print(f"      {link['href']}")
            else:
                print("❌ No scoring data available")
        else:
            print(f"❌ Analysis failed: {result.error_message}")