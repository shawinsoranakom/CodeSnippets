def test_config_examples():
    """Show example configurations"""

    print("\n📚 Example Configurations")
    print("=" * 50)

    examples = [
        {
            "name": "BM25 Scored Documentation Links",
            "config": LinkPreviewConfig(
                include_internal=True,
                include_external=False,
                include_patterns=["*/docs/*", "*/api/*", "*/reference/*"],
                query="API documentation reference guide",
                score_threshold=0.3,
                max_links=30,
                verbose=True
            )
        },
        {
            "name": "Internal Links Only",
            "config": LinkPreviewConfig(
                include_internal=True,
                include_external=False,
                max_links=50,
                verbose=True
            )
        },
        {
            "name": "External Links with Patterns",
            "config": LinkPreviewConfig(
                include_internal=False,
                include_external=True,
                include_patterns=["*github.com*", "*stackoverflow.com*"],
                max_links=20,
                concurrency=10
            )
        },
        {
            "name": "High-Performance Mode",
            "config": LinkPreviewConfig(
                include_internal=True,
                include_external=False,
                concurrency=20,
                timeout=3,
                max_links=100,
                verbose=False
            )
        }
    ]

    for example in examples:
        print(f"\n📝 {example['name']}:")
        print("   Configuration:")
        config_dict = example['config'].to_dict()
        for key, value in config_dict.items():
            print(f"     {key}: {value}")

        print("   Usage:")
        print("     from crawl4ai import LinkPreviewConfig")
        print("     config = CrawlerRunConfig(")
        print("         link_preview_config=LinkPreviewConfig(")
        for key, value in config_dict.items():
            if isinstance(value, str):
                print(f"             {key}='{value}',")
            elif isinstance(value, list) and value:
                print(f"             {key}={value},")
            elif value is not None:
                print(f"             {key}={value},")
        print("         )")
        print("     )")