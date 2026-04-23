def run_model(self) -> list[Data]:
        # Convert string values to enum instances with validation
        try:
            search_depth_enum = (
                self.search_depth
                if isinstance(self.search_depth, TavilySearchDepth)
                else TavilySearchDepth(str(self.search_depth).lower())
            )
        except ValueError as e:
            error_message = f"Invalid search depth value: {e!s}"
            self.status = error_message
            return [Data(data={"error": error_message})]

        try:
            topic_enum = (
                self.topic if isinstance(self.topic, TavilySearchTopic) else TavilySearchTopic(str(self.topic).lower())
            )
        except ValueError as e:
            error_message = f"Invalid topic value: {e!s}"
            self.status = error_message
            return [Data(data={"error": error_message})]

        try:
            time_range_enum = (
                self.time_range
                if isinstance(self.time_range, TavilySearchTimeRange)
                else TavilySearchTimeRange(str(self.time_range).lower())
                if self.time_range
                else None
            )
        except ValueError as e:
            error_message = f"Invalid time range value: {e!s}"
            self.status = error_message
            return [Data(data={"error": error_message})]

        # Initialize domain variables as None
        include_domains = None
        exclude_domains = None

        # Only process domains if they're provided
        if self.include_domains:
            include_domains = [domain.strip() for domain in self.include_domains.split(",") if domain.strip()]

        if self.exclude_domains:
            exclude_domains = [domain.strip() for domain in self.exclude_domains.split(",") if domain.strip()]

        return self._tavily_search(
            self.query,
            search_depth=search_depth_enum,
            topic=topic_enum,
            max_results=self.max_results,
            include_images=self.include_images,
            include_answer=self.include_answer,
            chunks_per_source=self.chunks_per_source,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            include_raw_content=self.include_raw_content,
            days=self.days,
            time_range=time_range_enum,
        )