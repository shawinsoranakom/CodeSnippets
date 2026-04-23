async def run(self, url="", query: str = "", search_type: str = "text", schema_cache_path = None, **kwargs) -> str:
        """Crawl Google Search results for a query"""
        url = f"https://www.google.com/search?q={query}&gl=sg&hl=en" if search_type == "text" else f"https://www.google.com/search?q={query}&gl=sg&hl=en&tbs=qdr:d&udm=2"
        if kwargs.get("page_start", 1) > 1:
            url = f"{url}&start={kwargs['page_start'] * 10}"
        if kwargs.get("page_length", 1) > 1:
            url = f"{url}&num={kwargs['page_length']}"

        browser_config = BrowserConfig(headless=True, verbose=True)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                cache_mode=kwargs.get("cache_mode", CacheMode.BYPASS),
                keep_attrs=["id", "class"],
                keep_data_attributes=True,
                delay_before_return_html=kwargs.get(
                    "delay", 2 if search_type == "image" else 1),
                js_code=self.js_script if search_type == "image" else None,
            )

            result = await crawler.arun(url=url, config=config)
            if not result.success:
                return json.dumps({"error": result.error})

            if search_type == "image":
                if result.js_execution_result.get("success", False) is False:
                    return json.dumps({"error": result.js_execution_result.get("error", "Unknown error")})
                if "results" in result.js_execution_result:
                    image_result = result.js_execution_result['results'][0]
                    if image_result.get("success", False) is False:
                        return json.dumps({"error": image_result.get("error", "Unknown error")})
                    return json.dumps(image_result["result"], indent=4)

            # For text search, extract structured data
            schemas = await self._build_schemas(result.cleaned_html, schema_cache_path)
            extracted = {
                key: JsonCssExtractionStrategy(schema=schemas[key]).run(
                    url=url, sections=[result.html]
                )
                for key in schemas
            }
            return json.dumps(extracted, indent=4)