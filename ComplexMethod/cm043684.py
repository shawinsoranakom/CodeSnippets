def transform_data(
        query: TmxAvailableIndicesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[TmxAvailableIndicesData]:
        """Transform the data to the standard format."""
        # pylint: disable=import-outside-toplevel
        import re

        data = data.copy()
        if data == {}:
            raise EmptyDataError

        # Extract the category for each index.
        symbols = {}
        for category, symbol_list in data["groups"].items():
            for symbol in symbol_list:
                if symbol not in symbols:
                    symbols[symbol] = category
                else:
                    symbols[symbol].append(category)
            category = {"category": symbols}  # noqa: PLW2901
        # Extract the data for each index and combine with the category.
        new_data = []
        for symbol in data["indices"]:
            overview = data["indices"][symbol].get("overview_en", None)
            if overview:
                # Remove HTML tags from the overview
                overview = re.sub("<.*?>", "", overview)
                # Remove additional artifacts from the overview
                overview = re.sub("\r|\n|amp;", "", overview)
            new_data.append(
                {
                    "symbol": symbol,
                    "name": data["indices"][symbol].get("name_en", None),
                    "currency": (
                        "USD"
                        if "(USD)" in data["indices"][symbol]["name_en"]
                        else "CAD"
                    ),
                    "category": symbols[symbol],
                    "market_value": (
                        data["indices"][symbol]["quotedmarketvalue"].get("total", None)
                        if data["indices"][symbol].get("quotedmarketvalue")
                        else None
                    ),
                    "num_constituents": data["indices"][symbol].get(
                        "nb_constituents", None
                    ),
                    "overview": (
                        overview
                        if data["indices"][symbol].get("overview") != ""
                        else None
                    ),
                    "methodology": (
                        data["indices"][symbol].get("methodology", None)
                        if data["indices"][symbol].get("methodology") != ""
                        else None
                    ),
                    "factsheet": (
                        data["indices"][symbol].get("factsheet", None)
                        if data["indices"][symbol].get("factsheet") != ""
                        else None
                    ),
                }
            )

        return [TmxAvailableIndicesData.model_validate(d) for d in new_data]