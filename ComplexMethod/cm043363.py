def _process_chunk(self, chunk_html: str, chunk_index: int, total_chunks: int, has_headers: bool = True) -> Dict[str, Any]:
        """
        Process a single chunk with the LLM.
        """
        if self.verbose:
            self._log("info", f"Processing chunk {chunk_index + 1}/{total_chunks}")

        # Build context about headers
        header_context = ""
        if not has_headers:
            header_context = "\nIMPORTANT: This table has NO headers. Return an empty array for 'headers' field and extract all rows as data rows."

        # Add context about this being part of a larger table
        chunk_prompt = f"""Extract table data from this HTML chunk.
This is part {chunk_index + 1} of {total_chunks} of a larger table.
Focus on extracting the data rows accurately.{header_context}

```html
{sanitize_html(chunk_html)}
```

Return only a JSON array of extracted tables following the specified format."""

        for attempt in range(1, self.max_tries + 1):
            try:
                if self.verbose and attempt > 1:
                    self._log("info", f"Retry attempt {attempt}/{self.max_tries} for chunk {chunk_index + 1}")

                response = perform_completion_with_backoff(
                    provider=self.llm_config.provider,
                    prompt_with_variables=self.TABLE_EXTRACTION_PROMPT + "\n\n" + chunk_prompt,
                    api_token=self.llm_config.api_token,
                    base_url=self.llm_config.base_url,
                    json_response=True,
                    base_delay=self.llm_config.backoff_base_delay,
                    max_attempts=self.llm_config.backoff_max_attempts,
                    exponential_factor=self.llm_config.backoff_exponential_factor,
                    extra_args=self.extra_args
                )

                if response and response.choices:
                    content = response.choices[0].message.content

                    # Parse JSON response
                    if isinstance(content, str):
                        tables_data = json.loads(content)
                    else:
                        tables_data = content

                    # Handle various response formats
                    if isinstance(tables_data, dict):
                        if 'result' in tables_data:
                            tables_data = tables_data['result']
                        elif 'tables' in tables_data:
                            tables_data = tables_data['tables']
                        elif 'data' in tables_data:
                            tables_data = tables_data['data']
                        else:
                            tables_data = [tables_data]

                    # Flatten nested lists
                    while isinstance(tables_data, list) and len(tables_data) == 1 and isinstance(tables_data[0], list):
                        tables_data = tables_data[0]

                    if not isinstance(tables_data, list):
                        tables_data = [tables_data]

                    # Return first valid table (each chunk should have one table)
                    for table in tables_data:
                        if self._validate_table_structure(table):
                            return {
                                'chunk_index': chunk_index,
                                'table': self._ensure_table_format(table)
                            }

                    # If no valid table, return empty result
                    return {'chunk_index': chunk_index, 'table': None}

            except Exception as e:
                if self.verbose:
                    self._log("error", f"Error processing chunk {chunk_index + 1}: {str(e)}")

                if attempt < self.max_tries:
                    time.sleep(1)
                    continue
                else:
                    return {'chunk_index': chunk_index, 'table': None, 'error': str(e)}

        return {'chunk_index': chunk_index, 'table': None}