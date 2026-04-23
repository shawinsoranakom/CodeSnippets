def crawl_urls_batch(search_results):
    url_to_search_results = {}
    unique_urls = []
    for search_result in search_results:
        if not search_result.get("url", False):
            continue
        if not search_result.get("is_scrapping_required", True):
            continue
        if not search_result.get('original_url'):
            search_result['original_url'] = search_result['url']
        url = search_result["url"]
        if url not in url_to_search_results:
            url_to_search_results[url] = []
            unique_urls.append(url)
        url_to_search_results[url].append(search_result)
    browser_crawler = create_browser_crawler()
    scraped_results = browser_crawler.scrape_urls(unique_urls)
    url_to_scraped = {result["original_url"]: result for result in scraped_results}
    updated_search_results = []
    successful_scrapes = 0
    failed_scrapes = 0
    for search_result in search_results:
        original_url = search_result["url"]
        scraped = url_to_scraped.get(original_url, {})
        updated_result = search_result.copy()
        updated_result["original_url"] = original_url
        if scraped.get("success", False):
            updated_result["url"] = scraped.get("final_url", original_url)
            updated_result["full_text"] = scraped.get("full_text", "")
            updated_result["published_date"] = scraped.get("published_date", "")
            successful_scrapes += 1
        else:
            updated_result["url"] = original_url
            updated_result["full_text"] = search_result.get("description", "")
            updated_result["published_date"] = ""
            failed_scrapes += 1
        updated_search_results.append(updated_result)
    return updated_search_results, successful_scrapes, failed_scrapes