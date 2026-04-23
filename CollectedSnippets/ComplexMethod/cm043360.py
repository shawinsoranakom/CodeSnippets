def extract_tables(self, element: etree.Element, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract tables from HTML using LLM.

        Args:
            element: The HTML element to search for tables
            **kwargs: Additional parameters

        Returns:
            List of dictionaries containing extracted table data
        """
        # Allow CSS selector override via kwargs
        css_selector = kwargs.get("css_selector", self.css_selector)

        # Get the HTML content to process
        if css_selector:
            # Use XPath to convert CSS selector (basic conversion)
            # For more complex CSS selectors, we might need a proper CSS to XPath converter
            selected_elements = self._css_to_xpath_select(element, css_selector)
            if not selected_elements:
                self._log("warning", f"No elements found for CSS selector: {css_selector}")
                return []
            html_content = ''.join(etree.tostring(elem, encoding='unicode') for elem in selected_elements)
        else:
            # Process entire element
            html_content = etree.tostring(element, encoding='unicode')

        # Check if there are any tables in the content
        if '<table' not in html_content.lower():
            if self.verbose:
                self._log("info", f"No <table> tags found in HTML content")
            return []

        if self.verbose:
            self._log("info", f"Found table tags in HTML, content length: {len(html_content)}")

        # Check if chunking is needed
        if self.enable_chunking and self._needs_chunking(html_content):
            if self.verbose:
                self._log("info", "Content exceeds token threshold, using chunked extraction")
            return self._extract_with_chunking(html_content)

        # Single extraction for small content
        # Prepare the prompt
        user_prompt = f"""GENERATE THE TABULATED DATA from the following HTML content:

```html
{sanitize_html(html_content)}
```

Return only a JSON array of extracted tables following the specified format."""

        # Try extraction with retries
        for attempt in range(1, self.max_tries + 1):
            try:
                if self.verbose and attempt > 1:
                    self._log("info", f"Retry attempt {attempt}/{self.max_tries} for table extraction")

                # Call LLM with the extraction prompt
                response = perform_completion_with_backoff(
                    provider=self.llm_config.provider,
                    prompt_with_variables=self.TABLE_EXTRACTION_PROMPT + "\n\n" + user_prompt + "\n\n MAKE SURE TO EXTRACT ALL DATA, DO NOT LEAVE ANYTHING FOR BRAVITY, YOUR GOAL IS TO RETURN ALL, NO MATTER HOW LONG IS DATA",
                    api_token=self.llm_config.api_token,
                    base_url=self.llm_config.base_url,
                    json_response=True,
                    base_delay=self.llm_config.backoff_base_delay,
                    max_attempts=self.llm_config.backoff_max_attempts,
                    exponential_factor=self.llm_config.backoff_exponential_factor,
                    extra_args=self.extra_args
                )

                # Parse the response
                if response and response.choices:
                    content = response.choices[0].message.content

                    if self.verbose:
                        self._log("debug", f"LLM response type: {type(content)}")
                        if isinstance(content, str):
                            self._log("debug", f"LLM response preview: {content[:200]}...")

                    # Parse JSON response
                    if isinstance(content, str):
                        tables_data = json.loads(content)
                    else:
                        tables_data = content

                    # Handle various response formats from LLM
                    # Sometimes LLM wraps response in "result" or other keys
                    if isinstance(tables_data, dict):
                        # Check for common wrapper keys
                        if 'result' in tables_data:
                            tables_data = tables_data['result']
                        elif 'tables' in tables_data:
                            tables_data = tables_data['tables']
                        elif 'data' in tables_data:
                            tables_data = tables_data['data']
                        else:
                            # If it's a single table dict, wrap in list
                            tables_data = [tables_data]

                    # Flatten nested lists if needed
                    while isinstance(tables_data, list) and len(tables_data) == 1 and isinstance(tables_data[0], list):
                        tables_data = tables_data[0]

                    # Ensure we have a list
                    if not isinstance(tables_data, list):
                        tables_data = [tables_data]

                    if self.verbose:
                        self._log("debug", f"Parsed {len(tables_data)} table(s) from LLM response")

                    # Validate and clean the extracted tables
                    validated_tables = []
                    for table in tables_data:
                        if self._validate_table_structure(table):
                            validated_tables.append(self._ensure_table_format(table))
                        elif self.verbose:
                            self._log("warning", f"Table failed validation: {table}")

                    # Check if we got valid tables
                    if validated_tables:
                        if self.verbose:
                            self._log("info", f"Successfully extracted {len(validated_tables)} tables using LLM on attempt {attempt}")
                        return validated_tables

                    # If no valid tables but we still have attempts left, retry
                    if attempt < self.max_tries:
                        if self.verbose:
                            self._log("warning", f"No valid tables extracted on attempt {attempt}, retrying...")
                        continue
                    else:
                        if self.verbose:
                            self._log("warning", f"No valid tables extracted after {self.max_tries} attempts")
                        return []

            except json.JSONDecodeError as e:
                if self.verbose:
                    self._log("error", f"JSON parsing error on attempt {attempt}: {str(e)}")
                if attempt < self.max_tries:
                    continue
                else:
                    return []

            except Exception as e:
                if self.verbose:
                    self._log("error", f"Error in LLM table extraction on attempt {attempt}: {str(e)}")
                    if attempt == self.max_tries:
                        import traceback
                        self._log("debug", f"Traceback: {traceback.format_exc()}")

                # For unexpected errors, retry if we have attempts left
                if attempt < self.max_tries:
                    # Add a small delay before retry for rate limiting
                    import time
                    time.sleep(1)
                    continue
                else:
                    return []

        # Should not reach here, but return empty list as fallback
        return []