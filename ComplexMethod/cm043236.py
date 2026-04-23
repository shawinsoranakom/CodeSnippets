async def agenerate_schema(
        html: str = None,
        schema_type: str = "CSS",
        query: str = None,
        target_json_example: str = None,
        llm_config: 'LLMConfig' = None,
        provider: str = None,
        api_token: str = None,
        url: Union[str, List[str]] = None,
        validate: bool = True,
        max_refinements: int = 3,
        usage: 'TokenUsage' = None,
        **kwargs
    ) -> dict:
        """
        Generate extraction schema from HTML content or URL(s) (async version).

        Use this method when calling from async contexts (e.g., FastAPI) to avoid
        issues with certain LLM providers (e.g., Gemini/Vertex AI) that require
        async execution.

        Args:
            html (str, optional): The HTML content to analyze. If not provided, url must be set.
            schema_type (str): "CSS" or "XPATH". Defaults to "CSS".
            query (str, optional): Natural language description of what data to extract.
            target_json_example (str, optional): Example of desired JSON output.
            llm_config (LLMConfig): LLM configuration object.
            provider (str): Legacy Parameter. LLM provider to use.
            api_token (str): Legacy Parameter. API token for LLM provider.
            url (str or List[str], optional): URL(s) to fetch HTML from. If provided, html parameter is ignored.
                When multiple URLs are provided, HTMLs are fetched in parallel and concatenated.
            validate (bool): If True, validate the schema against the HTML and
                refine via LLM feedback loop. Defaults to False (zero overhead).
            max_refinements (int): Max refinement rounds when validate=True. Defaults to 3.
            usage (TokenUsage, optional): Token usage accumulator. If provided,
                token counts from all LLM calls (including inference and
                validation retries) are added to it in-place.
            **kwargs: Additional args passed to LLM processor.

        Returns:
            dict: Generated schema following the JsonElementExtractionStrategy format.

        Raises:
            ValueError: If neither html nor url is provided.
        """
        from .utils import aperform_completion_with_backoff, preprocess_html_for_schema

        # Validate inputs
        if html is None and (url is None or (isinstance(url, list) and len(url) == 0)):
            raise ValueError("Either 'html' or 'url' must be provided")

        # Check deprecated parameters
        for name, message in JsonElementExtractionStrategy._GENERATE_SCHEMA_UNWANTED_PROPS.items():
            if locals()[name] is not None:
                raise AttributeError(f"Setting '{name}' is deprecated. {message}")

        if llm_config is None:
            llm_config = create_llm_config()

        # Save original HTML(s) before preprocessing (for validation against real HTML)
        original_htmls = []

        # Fetch HTML from URL(s) if provided
        if url is not None:
            from .async_webcrawler import AsyncWebCrawler
            from .async_configs import BrowserConfig, CrawlerRunConfig, CacheMode

            browser_config = BrowserConfig(
                headless=True,
                text_mode=True,
                light_mode=True,
            )
            crawler_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

            # Normalize to list
            urls = [url] if isinstance(url, str) else url

            async with AsyncWebCrawler(config=browser_config) as crawler:
                if len(urls) == 1:
                    result = await crawler.arun(url=urls[0], config=crawler_config)
                    if not result.success:
                        raise Exception(f"Failed to fetch URL '{urls[0]}': {result.error_message}")
                    if result.status_code >= 400:
                        raise Exception(f"HTTP {result.status_code} error for URL '{urls[0]}'")
                    html = result.html
                    original_htmls = [result.html]
                else:
                    results = await crawler.arun_many(urls=urls, config=crawler_config)
                    html_parts = []
                    for i, result in enumerate(results, 1):
                        if not result.success:
                            raise Exception(f"Failed to fetch URL '{result.url}': {result.error_message}")
                        if result.status_code >= 400:
                            raise Exception(f"HTTP {result.status_code} error for URL '{result.url}'")
                        original_htmls.append(result.html)
                        cleaned = preprocess_html_for_schema(
                            html_content=result.html,
                            text_threshold=2000,
                            attr_value_threshold=500,
                            max_size=500_000
                        )
                        header = HTML_EXAMPLE_DELIMITER.format(index=i)
                        html_parts.append(f"{header}\n{cleaned}")
                    html = "\n\n".join(html_parts)
        else:
            original_htmls = [html]

        # Preprocess HTML for schema generation (skip if already preprocessed from multiple URLs)
        if url is None or isinstance(url, str):
            html = preprocess_html_for_schema(
                html_content=html,
                text_threshold=2000,
                attr_value_threshold=500,
                max_size=500_000
            )

        # --- Resolve expected fields for strict validation ---
        expected_fields = None
        if validate:
            if target_json_example:
                # User provided target JSON — extract field names from it
                try:
                    if isinstance(target_json_example, str):
                        target_obj = json.loads(target_json_example)
                    else:
                        target_obj = target_json_example
                    expected_fields = JsonElementExtractionStrategy._extract_expected_fields(target_obj)
                except (json.JSONDecodeError, TypeError):
                    pass
            elif query:
                # No target JSON but query describes fields — infer via quick LLM call
                first_url = None
                if url is not None:
                    first_url = url if isinstance(url, str) else url[0]
                inferred = await JsonElementExtractionStrategy._infer_target_json(
                    query=query, html_snippet=html, llm_config=llm_config, url=first_url, usage=usage
                )
                if inferred:
                    expected_fields = JsonElementExtractionStrategy._extract_expected_fields(inferred)
                    # Also inject as target_json_example for the schema prompt
                    if not target_json_example:
                        target_json_example = json.dumps(inferred, indent=2)

        prompt = JsonElementExtractionStrategy._build_schema_prompt(html, schema_type, query, target_json_example)
        messages = [{"role": "user", "content": prompt}]

        prev_schema_json = None
        last_schema = None
        max_attempts = 1 + (max_refinements if validate else 0)

        for attempt in range(max_attempts):
            try:
                response = await aperform_completion_with_backoff(
                    provider=llm_config.provider,
                    prompt_with_variables=prompt,
                    json_response=True,
                    api_token=llm_config.api_token,
                    base_url=llm_config.base_url,
                    messages=messages,
                    extra_args=kwargs,
                )
                if usage is not None:
                    usage.completion_tokens += response.usage.completion_tokens
                    usage.prompt_tokens += response.usage.prompt_tokens
                    usage.total_tokens += response.usage.total_tokens
                raw = response.choices[0].message.content
                if not raw or not raw.strip():
                    raise ValueError("LLM returned an empty response")

                schema = json.loads(_strip_markdown_fences(raw))
                last_schema = schema
            except json.JSONDecodeError as e:
                # JSON parse failure — ask LLM to fix it
                if not validate or attempt >= max_attempts - 1:
                    raise Exception(f"Failed to parse schema JSON: {str(e)}")
                messages.append({"role": "assistant", "content": raw})
                messages.append({"role": "user", "content": (
                    f"Your response was not valid JSON. Parse error: {e}\n"
                    "Please return ONLY valid JSON, nothing else."
                )})
                continue
            except Exception as e:
                raise Exception(f"Failed to generate schema: {str(e)}")

            # If validation is off, return immediately (zero overhead path)
            if not validate:
                return schema

            # --- Validation feedback loop ---
            # Validate against original HTML(s); success if works on at least one
            best_result = None
            for orig_html in original_htmls:
                vr = JsonElementExtractionStrategy._validate_schema(
                    schema, orig_html, schema_type,
                    expected_fields=expected_fields,
                )
                if best_result is None or vr["populated_fields"] > best_result["populated_fields"]:
                    best_result = vr
                if vr["success"]:
                    break

            if best_result["success"]:
                return schema

            # Last attempt — return best-effort
            if attempt >= max_attempts - 1:
                return schema

            # Detect repeated schema
            current_json = json.dumps(schema, sort_keys=True)
            is_repeated = current_json == prev_schema_json
            prev_schema_json = current_json

            # Build feedback and extend conversation
            feedback = JsonElementExtractionStrategy._build_feedback_message(
                best_result, schema, attempt + 1, is_repeated
            )
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": feedback})

        # Should not reach here, but return last schema as safety net
        if last_schema is not None:
            return last_schema
        raise Exception("Failed to generate schema: no attempts succeeded")