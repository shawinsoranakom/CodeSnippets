async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        if not input_data.urls and not input_data.ids:
            raise ValueError("Either 'urls' or 'ids' must be provided")

        sdk_kwargs = {}

        # Prefer urls over ids
        if input_data.urls:
            sdk_kwargs["urls"] = input_data.urls
        elif input_data.ids:
            sdk_kwargs["ids"] = input_data.ids

        if input_data.text:
            sdk_kwargs["text"] = {"includeHtmlTags": True}

        # Handle highlights - only include if modified from defaults
        if input_data.highlights and (
            input_data.highlights.num_sentences != 1
            or input_data.highlights.highlights_per_url != 1
            or input_data.highlights.query is not None
        ):
            highlights_dict = {}
            highlights_dict["numSentences"] = input_data.highlights.num_sentences
            highlights_dict["highlightsPerUrl"] = (
                input_data.highlights.highlights_per_url
            )
            if input_data.highlights.query:
                highlights_dict["query"] = input_data.highlights.query
            sdk_kwargs["highlights"] = highlights_dict

        # Handle summary - only include if modified from defaults
        if input_data.summary and (
            input_data.summary.query is not None
            or input_data.summary.schema is not None
        ):
            summary_dict = {}
            if input_data.summary.query:
                summary_dict["query"] = input_data.summary.query
            if input_data.summary.schema:
                summary_dict["schema"] = input_data.summary.schema
            sdk_kwargs["summary"] = summary_dict

        if input_data.livecrawl:
            sdk_kwargs["livecrawl"] = input_data.livecrawl.value

        if input_data.livecrawl_timeout is not None:
            sdk_kwargs["livecrawl_timeout"] = input_data.livecrawl_timeout

        if input_data.subpages is not None:
            sdk_kwargs["subpages"] = input_data.subpages

        if input_data.subpage_target:
            sdk_kwargs["subpage_target"] = input_data.subpage_target

        # Handle extras - only include if modified from defaults
        if input_data.extras and (
            input_data.extras.links > 0 or input_data.extras.image_links > 0
        ):
            extras_dict = {}
            if input_data.extras.links:
                extras_dict["links"] = input_data.extras.links
            if input_data.extras.image_links:
                extras_dict["image_links"] = input_data.extras.image_links
            sdk_kwargs["extras"] = extras_dict

        # Always enable context for LLM-ready output
        sdk_kwargs["context"] = True

        aexa = AsyncExa(api_key=credentials.api_key.get_secret_value())
        response = await aexa.get_contents(**sdk_kwargs)

        converted_results = [
            ExaSearchResults.from_sdk(sdk_result)
            for sdk_result in response.results or []
        ]

        yield "results", converted_results

        for result in converted_results:
            yield "result", result

        if response.context:
            yield "context", response.context

        if response.statuses:
            yield "statuses", response.statuses

        if response.cost_dollars:
            yield "cost_dollars", response.cost_dollars
            self.merge_stats(
                NodeExecutionStats(provider_cost=response.cost_dollars.total)
            )