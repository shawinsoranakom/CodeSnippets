async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        sdk_kwargs = {
            "url": input_data.url,
            "num_results": input_data.number_of_results,
        }

        # Handle domains
        if input_data.include_domains:
            sdk_kwargs["include_domains"] = input_data.include_domains
        if input_data.exclude_domains:
            sdk_kwargs["exclude_domains"] = input_data.exclude_domains

        # Handle dates
        if input_data.start_crawl_date:
            sdk_kwargs["start_crawl_date"] = input_data.start_crawl_date.isoformat()
        if input_data.end_crawl_date:
            sdk_kwargs["end_crawl_date"] = input_data.end_crawl_date.isoformat()
        if input_data.start_published_date:
            sdk_kwargs["start_published_date"] = (
                input_data.start_published_date.isoformat()
            )
        if input_data.end_published_date:
            sdk_kwargs["end_published_date"] = input_data.end_published_date.isoformat()

        # Handle text filters
        if input_data.include_text:
            sdk_kwargs["include_text"] = input_data.include_text
        if input_data.exclude_text:
            sdk_kwargs["exclude_text"] = input_data.exclude_text

        if input_data.moderation:
            sdk_kwargs["moderation"] = input_data.moderation

        # check if we need to use find_similar_and_contents
        content_settings = process_contents_settings(input_data.contents)

        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())

        if content_settings:
            # Use find_similar_and_contents when contents are requested
            sdk_kwargs["text"] = content_settings.get("text", False)
            if "highlights" in content_settings:
                sdk_kwargs["highlights"] = content_settings["highlights"]
            if "summary" in content_settings:
                sdk_kwargs["summary"] = content_settings["summary"]
            response = await aexa.find_similar_and_contents(**sdk_kwargs)
        else:
            response = await aexa.find_similar(**sdk_kwargs)

        converted_results = [
            ExaSearchResults.from_sdk(sdk_result)
            for sdk_result in response.results or []
        ]

        yield "results", converted_results
        for result in converted_results:
            yield "result", result

        if response.context:
            yield "context", response.context

        if response.cost_dollars:
            yield "cost_dollars", response.cost_dollars
            self.merge_stats(
                NodeExecutionStats(provider_cost=response.cost_dollars.total)
            )