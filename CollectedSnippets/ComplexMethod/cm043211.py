async def aprocess_html(
        self,
        url: str,
        html: str,
        extracted_content: str,
        config: CrawlerRunConfig,
        screenshot_data: str,
        pdf_data: str,
        verbose: bool,
        **kwargs,
    ) -> CrawlResult:
        """
        Process HTML content using the provided configuration.

        Args:
            url: The URL being processed
            html: Raw HTML content
            extracted_content: Previously extracted content (if any)
            config: Configuration object controlling processing behavior
            screenshot_data: Screenshot data (if any)
            pdf_data: PDF data (if any)
            verbose: Whether to enable verbose logging
            **kwargs: Additional parameters for backwards compatibility

        Returns:
            CrawlResult: Processed result containing extracted and formatted content
        """
        # === PREFETCH MODE SHORT-CIRCUIT ===
        if getattr(config, 'prefetch', False):
            from .utils import quick_extract_links

            # Use base_url from config (for raw: URLs), redirected_url, or original url
            effective_url = getattr(config, 'base_url', None) or kwargs.get('redirected_url') or url
            links = quick_extract_links(html, effective_url)

            return CrawlResult(
                url=url,
                html=html,
                success=True,
                links=links,
                status_code=kwargs.get('status_code'),
                response_headers=kwargs.get('response_headers'),
                redirected_url=kwargs.get('redirected_url'),
                ssl_certificate=kwargs.get('ssl_certificate'),
                # All other fields default to None
            )
        # === END PREFETCH SHORT-CIRCUIT ===

        cleaned_html = ""
        try:
            _url = url if not kwargs.get("is_raw_html", False) else "Raw HTML"
            t1 = time.perf_counter()

            # Get scraping strategy and ensure it has a logger
            scraping_strategy = config.scraping_strategy
            if not scraping_strategy.logger:
                scraping_strategy.logger = self.logger

            # Process HTML content
            params = config.__dict__.copy()
            params.pop("url", None)
            # add keys from kwargs to params that doesn't exist in params
            params.update({k: v for k, v in kwargs.items()
                          if k not in params.keys()})

            ################################
            # Scraping Strategy Execution  #
            ################################
            result: ScrapingResult = scraping_strategy.scrap(
                url, html, **params)

            if result is None:
                raise ValueError(
                    f"Process HTML, Failed to extract content from the website: {url}"
                )

        except InvalidCSSSelectorError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(
                f"Process HTML, Failed to extract content from the website: {url}, error: {str(e)}"
            )

        # Extract results - handle both dict and ScrapingResult
        if isinstance(result, dict):
            cleaned_html = sanitize_input_encode(
                result.get("cleaned_html", ""))
            media = result.get("media", {})
            tables = media.pop("tables", []) if isinstance(media, dict) else []
            links = result.get("links", {})
            metadata = result.get("metadata", {})
        else:
            cleaned_html = sanitize_input_encode(result.cleaned_html)
            # media = result.media.model_dump()
            # tables = media.pop("tables", [])
            # links = result.links.model_dump()
            media = result.media.model_dump() if hasattr(result.media, 'model_dump') else result.media
            tables = media.pop("tables", []) if isinstance(media, dict) else []
            links = result.links.model_dump() if hasattr(result.links, 'model_dump') else result.links
            metadata = result.metadata

        fit_html = preprocess_html_for_schema(html_content=html, text_threshold= 500, max_size= 300_000)

        ################################
        # Generate Markdown            #
        ################################
        markdown_generator: Optional[MarkdownGenerationStrategy] = (
            config.markdown_generator or DefaultMarkdownGenerator()
        )

        # --- SELECT HTML SOURCE BASED ON CONTENT_SOURCE ---
        # Get the desired source from the generator config, default to 'cleaned_html'
        selected_html_source = getattr(markdown_generator, 'content_source', 'cleaned_html')

        # Define the source selection logic using dict dispatch
        html_source_selector = {
            "raw_html": lambda: html,  # The original raw HTML
            "cleaned_html": lambda: cleaned_html,  # The HTML after scraping strategy
            "fit_html": lambda: fit_html,  # The HTML after preprocessing for schema
        }

        markdown_input_html = cleaned_html  # Default to cleaned_html

        try:
            # Get the appropriate lambda function, default to returning cleaned_html if key not found
            source_lambda = html_source_selector.get(selected_html_source, lambda: cleaned_html)
            # Execute the lambda to get the selected HTML
            markdown_input_html = source_lambda()

            # Log which source is being used (optional, but helpful for debugging)
            # if self.logger and verbose:
            #     actual_source_used = selected_html_source if selected_html_source in html_source_selector else 'cleaned_html (default)'
            #     self.logger.debug(f"Using '{actual_source_used}' as source for Markdown generation for {url}", tag="MARKDOWN_SRC")

        except Exception as e:
            # Handle potential errors, especially from preprocess_html_for_schema
            if self.logger:
                self.logger.warning(
                    f"Error getting/processing '{selected_html_source}' for markdown source: {e}. Falling back to cleaned_html.",
                    tag="MARKDOWN_SRC"
                )
            # Ensure markdown_input_html is still the default cleaned_html in case of error
            markdown_input_html = cleaned_html
        # --- END: HTML SOURCE SELECTION ---

        # Uncomment if by default we want to use PruningContentFilter
        # if not config.content_filter and not markdown_generator.content_filter:
        #     markdown_generator.content_filter = PruningContentFilter()

        # Extract <base href> from raw HTML before it gets stripped by cleaning.
        # This ensures relative URLs resolve correctly even with cleaned_html.
        base_url = params.get("base_url") or params.get("redirected_url") or url
        base_tag_match = re.search(r'<base\s[^>]*href\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
        if base_tag_match:
            base_url = base_tag_match.group(1)

        markdown_result: MarkdownGenerationResult = (
            markdown_generator.generate_markdown(
                input_html=markdown_input_html,
                base_url=base_url
                # html2text_options=kwargs.get('html2text', {})
            )
        )

        # Log processing completion
        self.logger.url_status(
            url=_url,
            success=True,
            timing=int((time.perf_counter() - t1) * 1000) / 1000,
            tag="SCRAPE"
        )
        # self.logger.info(
        #     message="{url:.50}... | Time: {timing}s",
        #     tag="SCRAPE",
        #     params={"url": _url, "timing": int((time.perf_counter() - t1) * 1000) / 1000},
        # )

        ################################
        # Structured Content Extraction           #
        ################################
        if (
            not bool(extracted_content)
            and config.extraction_strategy
            and not isinstance(config.extraction_strategy, NoExtractionStrategy)
        ):
            t1 = time.perf_counter()
            # Choose content based on input_format
            content_format = config.extraction_strategy.input_format
            if content_format == "fit_markdown" and not markdown_result.fit_markdown:

                self.logger.url_status(
                        url=_url,
                        success=bool(html),
                        timing=time.perf_counter() - t1,
                        tag="EXTRACT",
                    )
                content_format = "markdown"

            content = {
                "markdown": markdown_result.raw_markdown,
                "html": html,
                "fit_html": fit_html,
                "cleaned_html": cleaned_html,
                "fit_markdown": markdown_result.fit_markdown,
            }.get(content_format, markdown_result.raw_markdown)

            # Use IdentityChunking for HTML input, otherwise use provided chunking strategy
            chunking = (
                IdentityChunking()
                if content_format in ["html", "cleaned_html", "fit_html"]
                else config.chunking_strategy
            )
            sections = chunking.chunk(content)
            # extracted_content = config.extraction_strategy.run(_url, sections)

            # Use async version if available for better parallelism
            if hasattr(config.extraction_strategy, 'arun'):
                extracted_content = await config.extraction_strategy.arun(_url, sections)
            else:
                # Fallback to sync version run in thread pool to avoid blocking
                extracted_content = await asyncio.to_thread(
                    config.extraction_strategy.run, url, sections
                )

            extracted_content = json.dumps(
                extracted_content, indent=4, default=str, ensure_ascii=False
            )

            # Log extraction completion
            self.logger.url_status(
                        url=_url,
                        success=bool(html),
                        timing=time.perf_counter() - t1,
                        tag="EXTRACT",
                    )

        # Apply HTML formatting if requested
        if config.prettiify:
            cleaned_html = fast_format_html(cleaned_html)

        # Return complete crawl result
        return CrawlResult(
            url=url,
            html=html,
            fit_html=fit_html,
            cleaned_html=cleaned_html,
            markdown=markdown_result,
            media=media,
            tables=tables,                       # NEW
            links=links,
            metadata=metadata,
            screenshot=screenshot_data,
            pdf=pdf_data,
            extracted_content=extracted_content,
            success=True,
            error_message="",
        )