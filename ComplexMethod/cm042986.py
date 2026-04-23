async def test_comprehensive_metadata_extraction(self, seeder):
        """Test extraction of all metadata types including JSON-LD."""
        config = SeedingConfig(
            source="sitemap",
            extract_head=True,
            query="match report",
            scoring_method="bm25",
            max_urls=5,
            verbose=True
        )

        results = await seeder.urls(TEST_DOMAIN, config)

        for result in results:
            head_data = result.get("head_data", {})

            # Check for various metadata fields
            print(f"\nMetadata for {result['url']}:")
            print(f"  Title: {head_data.get('title', 'N/A')}")
            print(f"  Charset: {head_data.get('charset', 'N/A')}")
            print(f"  Lang: {head_data.get('lang', 'N/A')}")

            # Check meta tags
            meta = head_data.get("meta", {})
            if meta:
                print("  Meta tags found:")
                for key in ["description", "keywords", "author", "viewport"]:
                    if key in meta:
                        print(f"    {key}: {meta[key][:50]}...")

            # Check for Open Graph tags
            og_tags = {k: v for k, v in meta.items() if k.startswith("og:")}
            if og_tags:
                print("  Open Graph tags found:")
                for k, v in list(og_tags.items())[:3]:
                    print(f"    {k}: {v[:50]}...")

            # Check JSON-LD
            if head_data.get("jsonld"):
                print(f"  JSON-LD schemas found: {len(head_data['jsonld'])}")