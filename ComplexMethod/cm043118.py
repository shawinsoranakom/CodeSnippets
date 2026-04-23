async def demo_deep_filtering_scoring(client: httpx.AsyncClient):
    """Demonstrates deep crawl with advanced URL filtering and scoring."""
    max_depth = 2  # Go a bit deeper to see scoring/filtering effects
    max_pages = 6
    excluded_pattern = "*/category-1/*"  # Example pattern to exclude
    keyword_to_score = "product"        # Example keyword to prioritize

    payload = {
        "urls": [DEEP_CRAWL_BASE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "stream": False,
                "cache_mode": "BYPASS",
                "deep_crawl_strategy": {
                    "type": "BFSDeepCrawlStrategy",
                    "params": {
                        "max_depth": max_depth,
                        "max_pages": max_pages,
                        "filter_chain": {
                            "type": "FilterChain",
                            "params": {
                                "filters": [
                                    {   # Stay on the allowed domain
                                        "type": "DomainFilter",
                                        "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}
                                    },
                                    {   # Only crawl HTML pages
                                        "type": "ContentTypeFilter",
                                        "params": {"allowed_types": ["text/html"]}
                                    },
                                    {   # Exclude URLs matching the pattern
                                        "type": "URLPatternFilter",
                                        "params": {
                                            "patterns": [excluded_pattern],
                                            "reverse": True  # Block if match
                                        }
                                    }
                                ]
                            }
                        },
                        "url_scorer": {
                            "type": "CompositeScorer",
                            "params": {
                                "scorers": [
                                    {   # Boost score for URLs containing the keyword
                                        "type": "KeywordRelevanceScorer",
                                        # Higher weight
                                        "params": {"keywords": [keyword_to_score], "weight": 1.5}
                                    },
                                    {   # Slightly penalize deeper pages
                                        "type": "PathDepthScorer",
                                        "params": {"optimal_depth": 1, "weight": -0.1}
                                    }
                                ]
                            }
                        },
                        # Optional: Only crawl URLs scoring above a threshold
                        # "score_threshold": 0.1
                    }
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 5c: Deep Crawl with Filtering & Scoring")

    # --- Verification/Analysis ---
    if results:
        console.print("[cyan]Deep Crawl Filtering/Scoring Analysis:[/]")
        excluded_found = False
        prioritized_found_at_depth1 = False
        prioritized_found_overall = False

        for result in results:
            url = result.get("url", "")
            depth = result.get("metadata", {}).get("depth", -1)

            # Check Filtering
            # Check if the excluded part is present
            if excluded_pattern.strip('*') in url:
                console.print(
                    f"  [bold red]Filter FAILED:[/bold red] Excluded pattern part '{excluded_pattern.strip('*')}' found in URL: {url}")
                excluded_found = True

            # Check Scoring (Observation)
            if keyword_to_score in url:
                prioritized_found_overall = True
                # Check if prioritized keywords appeared early (depth 1)
                if depth == 1:
                    prioritized_found_at_depth1 = True

        if not excluded_found:
            console.print(
                f"  [green]Filter Check:[/green] No URLs matching excluded pattern '{excluded_pattern}' found.")
        else:
            console.print(
                f"  [red]Filter Check:[/red] URLs matching excluded pattern '{excluded_pattern}' were found (unexpected).")

        if prioritized_found_at_depth1:
            console.print(
                f"  [green]Scoring Check:[/green] URLs with keyword '{keyword_to_score}' were found at depth 1 (scoring likely influenced).")
        elif prioritized_found_overall:
            console.print(
                f"  [yellow]Scoring Check:[/yellow] URLs with keyword '{keyword_to_score}' found, but not necessarily prioritized early (check max_pages/depth limits).")
        else:
            console.print(
                f"  [yellow]Scoring Check:[/yellow] No URLs with keyword '{keyword_to_score}' found within crawl limits.")