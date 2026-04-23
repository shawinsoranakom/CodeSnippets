async def run(
        self,
        input_data: Input,
        *,
        credentials: UserPasswordCredentials,
        **kwargs,
    ) -> BlockOutput:
        """Execute the related keywords query."""
        try:
            client = DataForSeoClient(credentials)

            results = await self._fetch_related_keywords(client, input_data)

            # Process and format the results
            related_keywords = []
            if results and len(results) > 0:
                # results is a list, get the first element
                first_result = results[0] if isinstance(results, list) else results
                # Handle missing key, null value, or valid list value
                if isinstance(first_result, dict):
                    items = first_result.get("items") or []
                else:
                    items = []
                for item in items:
                    # Extract keyword_data from the item
                    keyword_data = item.get("keyword_data", {})

                    # Create the RelatedKeyword object
                    keyword = RelatedKeyword(
                        keyword=keyword_data.get("keyword", ""),
                        search_volume=keyword_data.get("keyword_info", {}).get(
                            "search_volume"
                        ),
                        competition=keyword_data.get("keyword_info", {}).get(
                            "competition"
                        ),
                        cpc=keyword_data.get("keyword_info", {}).get("cpc"),
                        keyword_difficulty=keyword_data.get(
                            "keyword_properties", {}
                        ).get("keyword_difficulty"),
                        serp_info=(
                            keyword_data.get("serp_info")
                            if input_data.include_serp_info
                            else None
                        ),
                        clickstream_data=(
                            keyword_data.get("clickstream_keyword_info")
                            if input_data.include_clickstream_data
                            else None
                        ),
                    )
                    yield "related_keyword", keyword
                    related_keywords.append(keyword)

            yield "related_keywords", related_keywords
            yield "total_count", len(related_keywords)
            yield "seed_keyword", input_data.keyword
        except Exception as e:
            yield "error", f"Failed to fetch related keywords: {str(e)}"