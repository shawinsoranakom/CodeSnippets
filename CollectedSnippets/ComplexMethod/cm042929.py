def test_config_serialization_cycle():
    # Create original config
    original_config = create_test_config()

    # Dump to serializable dictionary
    serialized = original_config.dump()

    print(json.dumps(serialized, indent=2))

    # Load back into config object
    deserialized_config = CrawlerRunConfig.load(serialized)

    # Verify core attributes
    assert deserialized_config.word_count_threshold == original_config.word_count_threshold
    assert deserialized_config.css_selector == original_config.css_selector
    assert deserialized_config.excluded_tags == original_config.excluded_tags
    assert deserialized_config.keep_attrs == original_config.keep_attrs
    assert deserialized_config.cache_mode == original_config.cache_mode
    assert deserialized_config.wait_until == original_config.wait_until
    assert deserialized_config.page_timeout == original_config.page_timeout
    assert deserialized_config.scan_full_page == original_config.scan_full_page
    assert deserialized_config.verbose == original_config.verbose
    assert deserialized_config.stream == original_config.stream

    # Verify complex objects
    assert isinstance(deserialized_config.extraction_strategy, JsonCssExtractionStrategy)
    assert isinstance(deserialized_config.chunking_strategy, RegexChunking)
    assert isinstance(deserialized_config.markdown_generator, DefaultMarkdownGenerator)
    assert isinstance(deserialized_config.markdown_generator.content_filter, BM25ContentFilter)
    assert isinstance(deserialized_config.deep_crawl_strategy, BFSDeepCrawlStrategy)

    # Verify deep crawl strategy configuration
    assert deserialized_config.deep_crawl_strategy.max_depth == 3
    assert isinstance(deserialized_config.deep_crawl_strategy.filter_chain, FastFilterChain)
    assert isinstance(deserialized_config.deep_crawl_strategy.url_scorer, FastKeywordRelevanceScorer)

    print("Serialization cycle test passed successfully!")