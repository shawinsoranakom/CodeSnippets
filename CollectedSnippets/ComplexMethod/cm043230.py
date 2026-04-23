async def aextract(self, url: str, ix: int, html: str) -> List[Dict[str, Any]]:
        """
        Async version: Extract meaningful blocks or chunks from the given HTML using an LLM.

        How it works:
        1. Construct a prompt with variables.
        2. Make an async request to the LLM using the prompt.
        3. Parse the response and extract blocks or chunks.

        Args:
            url: The URL of the webpage.
            ix: Index of the block.
            html: The HTML content of the webpage.

        Returns:
            A list of extracted blocks or chunks.
        """
        from .utils import aperform_completion_with_backoff

        if self.verbose:
            print(f"[LOG] Call LLM for {url} - block index: {ix}")

        variable_values = {
            "URL": url,
            "HTML": escape_json_string(sanitize_html(html)),
        }

        prompt_with_variables = PROMPT_EXTRACT_BLOCKS
        if self.instruction:
            variable_values["REQUEST"] = self.instruction
            prompt_with_variables = PROMPT_EXTRACT_BLOCKS_WITH_INSTRUCTION

        if self.extract_type == "schema" and self.schema:
            variable_values["SCHEMA"] = json.dumps(self.schema, indent=2)
            prompt_with_variables = PROMPT_EXTRACT_SCHEMA_WITH_INSTRUCTION

        if self.extract_type == "schema" and not self.schema:
            prompt_with_variables = PROMPT_EXTRACT_INFERRED_SCHEMA

        for variable in variable_values:
            prompt_with_variables = prompt_with_variables.replace(
                "{" + variable + "}", variable_values[variable]
            )

        try:
            response = await aperform_completion_with_backoff(
                self.llm_config.provider,
                prompt_with_variables,
                self.llm_config.api_token,
                base_url=self.llm_config.base_url,
                json_response=self.force_json_response,
                extra_args=self.extra_args,
                base_delay=self.llm_config.backoff_base_delay,
                max_attempts=self.llm_config.backoff_max_attempts,
                exponential_factor=self.llm_config.backoff_exponential_factor
            )
            # Track usage
            usage = TokenUsage(
                completion_tokens=response.usage.completion_tokens,
                prompt_tokens=response.usage.prompt_tokens,
                total_tokens=response.usage.total_tokens,
                completion_tokens_details=response.usage.completion_tokens_details.__dict__
                if response.usage.completion_tokens_details
                else {},
                prompt_tokens_details=response.usage.prompt_tokens_details.__dict__
                if response.usage.prompt_tokens_details
                else {},
            )
            self.usages.append(usage)

            # Update totals
            self.total_usage.completion_tokens += usage.completion_tokens
            self.total_usage.prompt_tokens += usage.prompt_tokens
            self.total_usage.total_tokens += usage.total_tokens

            try:
                content = response.choices[0].message.content
                blocks = None

                if not content:
                    finish_reason = getattr(response.choices[0], "finish_reason", "unknown")
                    blocks = [{"index": 0, "error": True, "tags": ["error"],
                               "content": f"LLM returned no content (finish_reason: {finish_reason})"}]
                elif self.force_json_response:
                    blocks = json.loads(_strip_markdown_fences(content))
                    if isinstance(blocks, dict):
                        if len(blocks) == 1 and isinstance(list(blocks.values())[0], list):
                            blocks = list(blocks.values())[0]
                        else:
                            blocks = [blocks]
                    elif isinstance(blocks, list):
                        blocks = blocks
                else:
                    blocks = extract_xml_data(["blocks"], content)["blocks"]
                    blocks = json.loads(blocks)

                for block in blocks:
                    block["error"] = False
            except Exception:
                raw_content = response.choices[0].message.content or ""
                parsed, unparsed = split_and_parse_json_objects(raw_content)
                blocks = parsed
                if unparsed:
                    blocks.append(
                        {"index": 0, "error": True, "tags": ["error"], "content": unparsed}
                    )

            if self.verbose:
                print(
                    "[LOG] Extracted",
                    len(blocks),
                    "blocks from URL:",
                    url,
                    "block index:",
                    ix,
                )
            return blocks
        except Exception as e:
            if self.verbose:
                print(f"[LOG] Error in LLM extraction: {e}")
            return [
                {
                    "index": ix,
                    "error": True,
                    "tags": ["error"],
                    "content": str(e),
                }
            ]