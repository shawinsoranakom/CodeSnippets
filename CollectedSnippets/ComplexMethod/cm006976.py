def extract(self) -> Data:
        try:
            from firecrawl import FirecrawlApp
        except ImportError as e:
            msg = "Could not import firecrawl integration package. Please install it with `pip install firecrawl-py`."
            raise ImportError(msg) from e

        # Validate API key
        if not self.api_key:
            msg = "API key is required"
            raise ValueError(msg)

        # Validate URLs
        if not self.urls:
            msg = "URLs are required"
            raise ValueError(msg)

        # Split and validate URLs (handle both commas and newlines)
        urls = [url.strip() for url in self.urls.replace("\n", ",").split(",") if url.strip()]
        if not urls:
            msg = "No valid URLs provided"
            raise ValueError(msg)

        # Validate and process prompt
        if not self.prompt:
            msg = "Prompt is required"
            raise ValueError(msg)

        # Get the prompt text (handling both string and multiline input)
        prompt_text = self.prompt.strip()

        # Enhance the prompt to encourage comprehensive extraction
        enhanced_prompt = prompt_text
        if "schema" not in prompt_text.lower():
            enhanced_prompt = f"{prompt_text}. Please extract all instances in a comprehensive, structured format."

        params = {
            "prompt": enhanced_prompt,
            "enableWebSearch": self.enable_web_search,
            # Optional parameters - not essential for basic extraction
            "ignoreSitemap": self.ignore_sitemap,
            "includeSubdomains": self.include_subdomains,
            "showSources": self.show_sources,
            "timeout": 300,
        }

        # Only add schema to params if it's provided and is a valid schema structure
        if self.schema:
            try:
                if isinstance(self.schema, dict) and "type" in self.schema:
                    params["schema"] = self.schema
                elif hasattr(self.schema, "dict") and "type" in self.schema.dict():
                    params["schema"] = self.schema.dict()
                else:
                    # Skip invalid schema without raising an error
                    pass
            except Exception as e:  # noqa: BLE001
                logger.error(f"Invalid schema: {e!s}")

        try:
            app = FirecrawlApp(api_key=self.api_key)
            extract_result = app.extract(urls, params=params)
            return Data(data=extract_result)
        except Exception as e:
            msg = f"Error during extraction: {e!s}"
            raise ValueError(msg) from e