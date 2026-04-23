async def run(
        self,
        input_data: Input,
        *,
        credentials: UserPasswordCredentials,
        **kwargs,
    ) -> BlockOutput:
        """Execute the keyword suggestions query."""
        try:
            client = DataForSeoClient(credentials)

            results = await self._fetch_keyword_suggestions(client, input_data)

            # Process and format the results
            suggestions = []
            if results and len(results) > 0:
                # results is a list, get the first element
                first_result = results[0] if isinstance(results, list) else results
                items = (
                    first_result.get("items", [])
                    if isinstance(first_result, dict)
                    else []
                )
                if items is None:
                    items = []
                for item in items:
                    # Create the KeywordSuggestion object
                    suggestion = KeywordSuggestion(
                        keyword=item.get("keyword", ""),
                        search_volume=item.get("keyword_info", {}).get("search_volume"),
                        competition=item.get("keyword_info", {}).get("competition"),
                        cpc=item.get("keyword_info", {}).get("cpc"),
                        keyword_difficulty=item.get("keyword_properties", {}).get(
                            "keyword_difficulty"
                        ),
                        serp_info=(
                            item.get("serp_info")
                            if input_data.include_serp_info
                            else None
                        ),
                        clickstream_data=(
                            item.get("clickstream_keyword_info")
                            if input_data.include_clickstream_data
                            else None
                        ),
                    )
                    yield "suggestion", suggestion
                    suggestions.append(suggestion)

            yield "suggestions", suggestions
            yield "total_count", len(suggestions)
            yield "seed_keyword", input_data.keyword
        except Exception as e:
            yield "error", f"Failed to fetch keyword suggestions: {str(e)}"