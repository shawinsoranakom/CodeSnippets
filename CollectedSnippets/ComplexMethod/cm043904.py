def extract_data(
        query: ImfAvailableIndicatorsQueryParams,
        credentials: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict]:
        """Fetch the data."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError
        from openbb_imf.utils.metadata import ImfMetadata

        metadata = ImfMetadata()

        if isinstance(query.dataflows, str):
            dataflows = query.dataflows.split(",")
        elif isinstance(query.dataflows, list):
            dataflows = query.dataflows
        else:
            dataflows = None

        if isinstance(query.keywords, str):
            keywords = query.keywords.split(",")
        elif isinstance(query.keywords, list):
            keywords = query.keywords
        else:
            keywords = None

        try:
            results = metadata.search_indicators(
                query=query.query.replace(",", ", ") if query.query else "",
                dataflows=dataflows,
                keywords=keywords,
            )
        except Exception as e:  # pylint: disable=broad-except
            raise OpenBBError(e) from e

        if not results:
            raise EmptyDataError("No indicators found for the given query.")

        return results