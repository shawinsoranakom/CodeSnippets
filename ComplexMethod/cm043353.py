def crawl_cmd(url: str, browser_config: str, crawler_config: str, filter_config: str,
           extraction_config: str, json_extract: str, schema: str, browser: Dict, crawler: Dict,
           output: str, output_file: str, bypass_cache: bool, question: str, verbose: bool, profile: str, deep_crawl: str, max_pages: int, json_ensure_ascii: Optional[bool]):
    """Crawl a website and extract content

    Simple Usage:
        crwl crawl https://example.com
    """

    # Handle profile option
    if profile:
        profiler = BrowserProfiler()
        profile_path = profiler.get_profile_path(profile)

        if not profile_path:
            profiles = profiler.list_profiles()

            if profiles:
                console.print(f"[red]Profile '{profile}' not found. Available profiles:[/red]")
                display_profiles_table(profiles)
            else:
                console.print("[red]No profiles found. Create one with 'crwl profiles'[/red]")

            return

        # Include the profile in browser config
        if not browser:
            browser = {}
        browser["user_data_dir"] = profile_path
        browser["use_managed_browser"] = True

        if verbose:
            console.print(f"[green]Using browser profile:[/green] {profile}")

    try:
        # Load base configurations
        browser_cfg = BrowserConfig.load(load_config_file(browser_config))
        crawler_cfg = CrawlerRunConfig.load(load_config_file(crawler_config))

        # Override with CLI params
        if browser:
            browser_cfg = browser_cfg.clone(**browser)
        if crawler:
            crawler_cfg = crawler_cfg.clone(**crawler)

        # Handle content filter config
        if filter_config or output in ["markdown-fit", "md-fit"]:
            if filter_config:
                filter_conf = load_config_file(filter_config)
            elif not filter_config and output in ["markdown-fit", "md-fit"]:
                filter_conf = {
                    "type": "pruning",
                    "query": "",
                    "threshold": 0.48
                }
            if filter_conf["type"] == "bm25":
                crawler_cfg.markdown_generator = DefaultMarkdownGenerator(
                    content_filter = BM25ContentFilter(
                        user_query=filter_conf.get("query"),
                        bm25_threshold=filter_conf.get("threshold", 1.0),
                        use_stemming=filter_conf.get("use_stemming", True),
                    )
                )
            elif filter_conf["type"] == "pruning":
                crawler_cfg.markdown_generator = DefaultMarkdownGenerator(
                    content_filter = PruningContentFilter(
                        user_query=filter_conf.get("query"),
                        threshold=filter_conf.get("threshold", 0.48)
                    )
                )

        # Handle json-extract option (takes precedence over extraction-config)
        if json_extract is not None:
            # Get LLM provider and token
            provider, token = setup_llm_config()

            # Default sophisticated instruction for structured data extraction
            default_instruction = """Analyze the web page content and extract structured data as JSON. 
If the page contains a list of items with repeated patterns, extract all items in an array. 
If the page is an article or contains unique content, extract a comprehensive JSON object with all relevant information.
Look at the content, intention of content, what it offers and find the data item(s) in the page.
Always return valid, properly formatted JSON."""


            default_instruction_with_user_query = """Analyze the web page content and extract structured data as JSON, following the below instruction and explanation of schema and always return valid, properly formatted JSON. \n\nInstruction:\n\n""" + json_extract

            # Determine instruction based on whether json_extract is empty or has content
            instruction = default_instruction_with_user_query if json_extract else default_instruction

            # Create LLM extraction strategy
            crawler_cfg.extraction_strategy = LLMExtractionStrategy(
                llm_config=LLMConfig(provider=provider, api_token=token),
                instruction=instruction,
                schema=load_schema_file(schema),  # Will be None if no schema is provided
                extraction_type="schema", #if schema else "block",
                apply_chunking=False,
                force_json_response=True,
                verbose=verbose,
            )

            # Set output to JSON if not explicitly specified
            if output == "all":
                output = "json"

        # Handle extraction strategy from config file (only if json-extract wasn't used)
        elif extraction_config:
            extract_conf = load_config_file(extraction_config)
            schema_data = load_schema_file(schema)

            # Check if type does not exist show proper message
            if not extract_conf.get("type"):
                raise click.ClickException("Extraction type not specified")
            if extract_conf["type"] not in ["llm", "json-css", "json-xpath"]:
                raise click.ClickException(f"Invalid extraction type: {extract_conf['type']}")

            if extract_conf["type"] == "llm":
                # if no provider show error emssage
                if not extract_conf.get("provider") or not extract_conf.get("api_token"):
                    raise click.ClickException("LLM provider and API token are required for LLM extraction")

                crawler_cfg.extraction_strategy = LLMExtractionStrategy(
                    llm_config=LLMConfig(provider=extract_conf["provider"], api_token=extract_conf["api_token"]),
                    instruction=extract_conf["instruction"],
                    schema=schema_data,
                    **extract_conf.get("params", {})
                )
            elif extract_conf["type"] == "json-css":
                crawler_cfg.extraction_strategy = JsonCssExtractionStrategy(
                    schema=schema_data
                )
            elif extract_conf["type"] == "json-xpath":
                crawler_cfg.extraction_strategy = JsonXPathExtractionStrategy(
                    schema=schema_data
                )


        # No cache
        if bypass_cache:
            crawler_cfg.cache_mode = CacheMode.BYPASS

        crawler_cfg.scraping_strategy = LXMLWebScrapingStrategy()    

        # Handle deep crawling configuration
        if deep_crawl:
            if deep_crawl == "bfs":
                crawler_cfg.deep_crawl_strategy = BFSDeepCrawlStrategy(
                    max_depth=3,
                    max_pages=max_pages
                )
            elif deep_crawl == "dfs":
                crawler_cfg.deep_crawl_strategy = DFSDeepCrawlStrategy(
                    max_depth=3,
                    max_pages=max_pages
                )
            elif deep_crawl == "best-first":
                crawler_cfg.deep_crawl_strategy = BestFirstCrawlingStrategy(
                    max_depth=3,
                    max_pages=max_pages
                )

            if verbose:
                console.print(f"[green]Deep crawling enabled:[/green] {deep_crawl} strategy, max {max_pages} pages")

        config = get_global_config()

        browser_cfg.verbose = config.get("VERBOSE", False)
        crawler_cfg.verbose = config.get("VERBOSE", False)

        # Get JSON output config (priority: CLI flag > global config)
        if json_ensure_ascii is not None:
            ensure_ascii = json_ensure_ascii
        else:
            ensure_ascii = config.get("JSON_ENSURE_ASCII", USER_SETTINGS["JSON_ENSURE_ASCII"]["default"])

        # Run crawler
        result : CrawlResult = anyio.run(
            run_crawler,
            url,
            browser_cfg,
            crawler_cfg,
            verbose
        )

        # Handle deep crawl results (list) vs single result
        if isinstance(result, list):
            if len(result) == 0:
                click.echo("No results found during deep crawling")
                return
            # Use the first result for question answering and output
            main_result = result[0]
            all_results = result
        else:
            # Single result from regular crawling
            main_result = result
            all_results = [result]

        # Handle question
        if question:
            provider, token = setup_llm_config()
            markdown = main_result.markdown.raw_markdown
            anyio.run(stream_llm_response, url, markdown, question, provider, token)
            return

        # Handle output
        if not output_file:
            if output == "all":
                if isinstance(result, list):
                    output_data = [r.model_dump() for r in all_results]
                    click.echo(json.dumps(output_data, indent=2, ensure_ascii=ensure_ascii))
                else:
                    click.echo(json.dumps(main_result.model_dump(), indent=2, ensure_ascii=ensure_ascii))
            elif output == "json":
                print(main_result.extracted_content)
                extracted_items = json.loads(main_result.extracted_content)
                click.echo(json.dumps(extracted_items, indent=2, ensure_ascii=ensure_ascii))

            elif output in ["markdown", "md"]:
                if isinstance(result, list):
                    # Combine markdown from all crawled pages for deep crawl
                    for r in all_results:
                        click.echo(f"\n\n{'='*60}\n# {r.url}\n{'='*60}\n\n")
                        click.echo(r.markdown.raw_markdown)
                else:
                    click.echo(main_result.markdown.raw_markdown)
            elif output in ["markdown-fit", "md-fit"]:
                if isinstance(result, list):
                    # Combine fit markdown from all crawled pages for deep crawl
                    for r in all_results:
                        click.echo(f"\n\n{'='*60}\n# {r.url}\n{'='*60}\n\n")
                        click.echo(r.markdown.fit_markdown)
                else:
                    click.echo(main_result.markdown.fit_markdown)
        else:
            if output == "all":
                with open(output_file, "w", encoding="utf-8") as f:
                    if isinstance(result, list):
                        output_data = [r.model_dump() for r in all_results]
                        f.write(json.dumps(output_data, indent=2, ensure_ascii=ensure_ascii))
                    else:
                        f.write(json.dumps(main_result.model_dump(), indent=2, ensure_ascii=ensure_ascii))
            elif output == "json":
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(main_result.extracted_content)
            elif output in ["markdown", "md"]:
                with open(output_file, "w", encoding="utf-8") as f:
                    if isinstance(result, list):
                        # Combine markdown from all crawled pages for deep crawl
                        for r in all_results:
                            f.write(f"\n\n{'='*60}\n# {r.url}\n{'='*60}\n\n")
                            f.write(r.markdown.raw_markdown)
                    else:
                        f.write(main_result.markdown.raw_markdown)
            elif output in ["markdown-fit", "md-fit"]:
                with open(output_file, "w", encoding="utf-8") as f:
                    if isinstance(result, list):
                        # Combine fit markdown from all crawled pages for deep crawl
                        for r in all_results:
                            f.write(f"\n\n{'='*60}\n# {r.url}\n{'='*60}\n\n")
                            f.write(r.markdown.fit_markdown)
                    else:
                        f.write(main_result.markdown.fit_markdown)

    except Exception as e:
        raise click.ClickException(str(e))