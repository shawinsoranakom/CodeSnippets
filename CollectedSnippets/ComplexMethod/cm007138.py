def _tavily_search(
        self,
        query: str,
        *,
        search_depth: TavilySearchDepth = TavilySearchDepth.BASIC,
        topic: TavilySearchTopic = TavilySearchTopic.GENERAL,
        max_results: int = 5,
        include_images: bool = False,
        include_answer: bool = False,
        chunks_per_source: int = MAX_CHUNKS_PER_SOURCE,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        include_raw_content: bool = False,
        days: int = 7,
        time_range: TavilySearchTimeRange | None = None,
    ) -> list[Data]:
        # Validate enum values
        if not isinstance(search_depth, TavilySearchDepth):
            msg = f"Invalid search_depth value: {search_depth}"
            raise TypeError(msg)
        if not isinstance(topic, TavilySearchTopic):
            msg = f"Invalid topic value: {topic}"
            raise TypeError(msg)

        # Validate chunks_per_source range
        if not 1 <= chunks_per_source <= MAX_CHUNKS_PER_SOURCE:
            msg = f"chunks_per_source must be between 1 and {MAX_CHUNKS_PER_SOURCE}, got {chunks_per_source}"
            raise ValueError(msg)

        # Validate days is positive
        if days < 1:
            msg = f"days must be greater than or equal to 1, got {days}"
            raise ValueError(msg)

        try:
            url = "https://api.tavily.com/search"
            headers = {
                "content-type": "application/json",
                "accept": "application/json",
            }
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth.value,
                "topic": topic.value,
                "max_results": max_results,
                "include_images": include_images,
                "include_answer": include_answer,
                "chunks_per_source": chunks_per_source if search_depth == TavilySearchDepth.ADVANCED else None,
                "include_domains": include_domains if include_domains else None,
                "exclude_domains": exclude_domains if exclude_domains else None,
                "include_raw_content": include_raw_content,
                "days": days if topic == TavilySearchTopic.NEWS else None,
                "time_range": time_range.value if time_range else None,
            }

            with httpx.Client(timeout=90.0) as client:
                response = client.post(url, json=payload, headers=headers)

            response.raise_for_status()
            search_results = response.json()

            data_results = [
                Data(
                    data={
                        "title": result.get("title"),
                        "url": result.get("url"),
                        "content": result.get("content"),
                        "score": result.get("score"),
                        "raw_content": result.get("raw_content") if include_raw_content else None,
                    }
                )
                for result in search_results.get("results", [])
            ]

            if include_answer and search_results.get("answer"):
                data_results.insert(0, Data(data={"answer": search_results["answer"]}))

            if include_images and search_results.get("images"):
                data_results.append(Data(data={"images": search_results["images"]}))

            self.status = data_results  # type: ignore[assignment]

        except httpx.TimeoutException as e:
            error_message = "Request timed out (90s). Please try again or adjust parameters."
            logger.error(f"Timeout error: {e}")
            self.status = error_message
            raise ToolException(error_message) from e
        except httpx.HTTPStatusError as e:
            error_message = f"HTTP error: {e.response.status_code} - {e.response.text}"
            logger.debug(error_message)
            self.status = error_message
            raise ToolException(error_message) from e
        except Exception as e:
            error_message = f"Unexpected error: {e}"
            logger.debug("Error running Tavily Search", exc_info=True)
            self.status = error_message
            raise ToolException(error_message) from e
        return data_results