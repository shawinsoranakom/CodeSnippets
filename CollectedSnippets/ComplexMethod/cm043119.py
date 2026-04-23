async def demo_deep_with_css_extraction(client: httpx.AsyncClient):
    # Schema to extract H1 and first paragraph from any page
    general_schema = {
        "name": "PageContent",
        "baseSelector": "body",  # Apply to whole body
        "fields": [
            {"name": "page_title", "selector": "h1",
                "type": "text", "default": "N/A"},
            {"name": "first_p", "selector": "p", "type": "text",
                "default": "N/A"},  # Gets first p tag
        ]
    }
    payload = {
        "urls": [DEEP_CRAWL_BASE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "extraction_strategy": {  # Apply CSS extraction to each page
                    "type": "JsonCssExtractionStrategy",
                    "params": {"schema": {"type": "dict", "value": general_schema}}
                },
                "deep_crawl_strategy": {
                    "type": "BFSDeepCrawlStrategy",
                    "params": {
                        "max_depth": 1,
                        "max_pages": 3,
                        "filter_chain": {
                            "type": "FilterChain",
                            "params": {"filters": [
                                {"type": "DomainFilter", "params": {
                                    "allowed_domains": [DEEP_CRAWL_DOMAIN]}},
                                {"type": "ContentTypeFilter", "params": {
                                    "allowed_types": ["text/html"]}}
                            ]}
                        }
                    }
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 6a: Deep Crawl + CSS Extraction")

    if results:
        console.print("[cyan]CSS Extraction Summary from Deep Crawl:[/]")
        for result in results:
            if result.get("success") and result.get("extracted_content"):
                try:
                    extracted = json.loads(result["extracted_content"])
                    if isinstance(extracted, list) and extracted:
                        extracted = extracted[0]  # Use first item
                    title = extracted.get(
                        'page_title', 'N/A') if isinstance(extracted, dict) else 'Parse Error'
                    console.print(
                        f"  [green]✔[/] URL: [link={result['url']}]{result['url']}[/link] | Title: {title}")
                except Exception:
                    console.print(
                        f"  [yellow]![/] URL: [link={result['url']}]{result['url']}[/link] | Failed to parse extracted content")
            elif result.get("success"):
                console.print(
                    f"  [yellow]-[/] URL: [link={result['url']}]{result['url']}[/link] | No content extracted.")
            else:
                console.print(
                    f"  [red]✘[/] URL: [link={result['url']}]{result['url']}[/link] | Crawl failed.")