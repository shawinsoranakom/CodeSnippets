def filter_content(self, html: str, ignore_cache: bool = True) -> List[str]:
        if not html or not isinstance(html, str):
            return []

        if self.logger:
            self.logger.info(
                "Starting LLM markdown content filtering process",
                tag="LLM",
                params={"provider": self.llm_config.provider},
                colors={"provider": LogColor.CYAN},
            )

        # Cache handling
        cache_dir = Path(get_home_folder()) / "llm_cache" / "content_filter"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_key = self._get_cache_key(html, self.instruction or "")
        cache_file = cache_dir / f"{cache_key}.json"

        # if ignore_cache == None:
        ignore_cache = self.ignore_cache

        if not ignore_cache and cache_file.exists():
            if self.logger:
                self.logger.info("Found  cached markdown result", tag="CACHE")
            try:
                with cache_file.open("r") as f:
                    cached_data = json.load(f)
                    usage = TokenUsage(**cached_data["usage"])
                    self.usages.append(usage)
                    self.total_usage.completion_tokens += usage.completion_tokens
                    self.total_usage.prompt_tokens += usage.prompt_tokens
                    self.total_usage.total_tokens += usage.total_tokens
                    return cached_data["blocks"]
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        f"LLM markdown: Cache read error: {str(e)}", tag="CACHE"
                    )

        # Split into chunks
        html_chunks = self._merge_chunks(html)
        if self.logger:
            self.logger.info(
                "LLM markdown: Split content into {chunk_count} chunks",
                tag="CHUNK",
                params={"chunk_count": len(html_chunks)},
                colors={"chunk_count": LogColor.YELLOW},
            )

        start_time = time.time()

        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i, chunk in enumerate(html_chunks):
                if self.logger:
                    self.logger.debug(
                        "LLM markdown: Processing chunk {chunk_num}/{total_chunks}",
                        tag="CHUNK",
                        params={"chunk_num": i + 1, "total_chunks": len(html_chunks)},
                    )

                prompt_variables = {
                    "HTML": escape_json_string(sanitize_html(chunk)),
                    "REQUEST": self.instruction
                    or "Convert this HTML into clean, relevant markdown, removing any noise or irrelevant content.",
                }

                prompt = PROMPT_FILTER_CONTENT
                for var, value in prompt_variables.items():
                    prompt = prompt.replace("{" + var + "}", value)

                def _proceed_with_chunk(
                    provider: str,
                    prompt: str,
                    api_token: str,
                    base_url: Optional[str] = None,
                    extra_args: Dict = {},
                ) -> List[str]:
                    if self.logger:
                        self.logger.info(
                            "LLM Markdown: Processing chunk {chunk_num}",
                            tag="CHUNK",
                            params={"chunk_num": i + 1},
                        )
                    return perform_completion_with_backoff(
                        provider,
                        prompt,
                        api_token,
                        base_url=base_url,
                        base_delay=self.llm_config.backoff_base_delay,
                        max_attempts=self.llm_config.backoff_max_attempts,
                        exponential_factor=self.llm_config.backoff_exponential_factor,
                        extra_args=extra_args,
                    )

                future = executor.submit(
                    _proceed_with_chunk,
                    self.llm_config.provider,
                    prompt,
                    self.llm_config.api_token,
                    self.llm_config.base_url,
                    self.extra_args,
                )
                futures.append((i, future))

            # Collect results in order
            ordered_results = []
            for i, future in sorted(futures):
                try:
                    response = future.result()

                    # Track usage
                    usage = TokenUsage(
                        completion_tokens=response.usage.completion_tokens,
                        prompt_tokens=response.usage.prompt_tokens,
                        total_tokens=response.usage.total_tokens,
                        completion_tokens_details=(
                            response.usage.completion_tokens_details.__dict__
                            if response.usage.completion_tokens_details
                            else {}
                        ),
                        prompt_tokens_details=(
                            response.usage.prompt_tokens_details.__dict__
                            if response.usage.prompt_tokens_details
                            else {}
                        ),
                    )
                    self.usages.append(usage)
                    self.total_usage.completion_tokens += usage.completion_tokens
                    self.total_usage.prompt_tokens += usage.prompt_tokens
                    self.total_usage.total_tokens += usage.total_tokens

                    blocks = extract_xml_data(
                        ["content"], response.choices[0].message.content
                    )["content"]
                    if blocks:
                        ordered_results.append(blocks)
                        if self.logger:
                            self.logger.success(
                                "LLM markdown: Successfully processed chunk {chunk_num}",
                                tag="CHUNK",
                                params={"chunk_num": i + 1},
                            )
                except Exception as e:
                    if self.logger:
                        self.logger.error(
                            "LLM markdown: Error processing chunk {chunk_num}: {error}",
                            tag="CHUNK",
                            params={"chunk_num": i + 1, "error": str(e)},
                        )

        end_time = time.time()
        if self.logger:
            self.logger.success(
                "LLM markdown: Completed processing in {time:.2f}s",
                tag="LLM",
                params={"time": end_time - start_time},
                colors={"time": LogColor.YELLOW},
            )

        result = ordered_results if ordered_results else []

        # Cache the final result
        cache_data = {"blocks": result, "usage": self.total_usage.__dict__}
        with cache_file.open("w") as f:
            json.dump(cache_data, f)
            if self.logger:
                self.logger.info("Cached results for future use", tag="CACHE")

        return result