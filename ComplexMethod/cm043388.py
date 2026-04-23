def process_html(
        self,
        url: str,
        html: str,
        extracted_content: str,
        word_count_threshold: int,
        extraction_strategy: ExtractionStrategy,
        chunking_strategy: ChunkingStrategy,
        css_selector: str,
        screenshot: bool,
        verbose: bool,
        is_cached: bool,
        **kwargs,
    ) -> CrawlResult:
        t = time.time()
        # Extract content from HTML
        try:
            t1 = time.time()
            scrapping_strategy = WebScrapingStrategy()
            extra_params = {
                k: v
                for k, v in kwargs.items()
                if k not in ["only_text", "image_description_min_word_threshold"]
            }
            result = scrapping_strategy.scrap(
                url,
                html,
                word_count_threshold=word_count_threshold,
                css_selector=css_selector,
                only_text=kwargs.get("only_text", False),
                image_description_min_word_threshold=kwargs.get(
                    "image_description_min_word_threshold",
                    IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD,
                ),
                **extra_params,
            )

            # result = get_content_of_website_optimized(url, html, word_count_threshold, css_selector=css_selector, only_text=kwargs.get("only_text", False))
            if verbose:
                print(
                    f"[LOG] 🚀 Content extracted for {url}, success: True, time taken: {time.time() - t1:.2f} seconds"
                )

            if result is None:
                raise ValueError(f"Failed to extract content from the website: {url}")
        except InvalidCSSSelectorError as e:
            raise ValueError(str(e))

        cleaned_html = sanitize_input_encode(result.get("cleaned_html", ""))
        markdown = sanitize_input_encode(result.get("markdown", ""))
        media = result.get("media", [])
        links = result.get("links", [])
        metadata = result.get("metadata", {})

        if extracted_content is None:
            if verbose:
                print(
                    f"[LOG] 🔥 Extracting semantic blocks for {url}, Strategy: {extraction_strategy.name}"
                )

            sections = chunking_strategy.chunk(markdown)
            extracted_content = extraction_strategy.run(url, sections)
            extracted_content = json.dumps(
                extracted_content, indent=4, default=str, ensure_ascii=False
            )

            if verbose:
                print(
                    f"[LOG] 🚀 Extraction done for {url}, time taken: {time.time() - t:.2f} seconds."
                )

        screenshot = None if not screenshot else screenshot

        if not is_cached:
            cache_url(
                url,
                html,
                cleaned_html,
                markdown,
                extracted_content,
                True,
                json.dumps(media),
                json.dumps(links),
                json.dumps(metadata),
                screenshot=screenshot,
            )

        return CrawlResult(
            url=url,
            html=html,
            cleaned_html=format_html(cleaned_html),
            markdown=markdown,
            media=media,
            links=links,
            metadata=metadata,
            screenshot=screenshot,
            extracted_content=extracted_content,
            success=True,
            error_message="",
        )