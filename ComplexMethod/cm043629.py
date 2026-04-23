def transform_query(params: dict[str, Any]) -> FredBondIndicesQueryParams:
        """Transform query."""
        values = params.copy()
        new_index = []
        messages = []
        values.setdefault("index", "yield_curve")
        values.setdefault("category", "us")
        values.setdefault("index_type", "yield")
        is_yield_curve = False
        if "yield_curve" in values["index"]:
            values["category"] = "us"
            values["index"] = "yield_curve"
            new_index.append("yield_curve")
            is_yield_curve = True
            if (
                isinstance(values["index"], list)
                and len(values["index"] > 1)  # type: ignore
                or isinstance(values["index"], str)
                and "," in values["index"]
            ):
                message = "Multiple indices not allowed for: 'yield_curve'."
                messages.append(message)
        if is_yield_curve is False:
            indices = (
                values["index"]
                if isinstance(values["index"], list)
                else values["index"].split(",")
            )
            for index in indices:
                if values["category"] == "us":
                    if index not in BAML_CATEGORIES.get("us"):  # type: ignore
                        message = (
                            f"Invalid index, {index}, for category: 'us'."
                            + f" Must be one of {', '.join(BAML_CATEGORIES.get('us'))}."  # type: ignore
                        )
                        messages.append(message)
                    elif (
                        index == "seasoned_corporate"
                        and values["index_type"] != "yield"
                    ):
                        message = (
                            "Invalid index_type for index: 'seasoned_corporate'."
                            + " Must be 'yield'."
                        )
                        messages.append(message)
                    else:
                        new_index.append(index)
                if values["category"] == "high_yield":
                    if index not in ("us", "europe", "emerging"):
                        message = (
                            f"Invalid index, {index}, for category: 'high_yield'."
                            + f" Must be one of {', '.join(BAML_CATEGORIES.get('high_yield', ''))}."  # type: ignore
                        )
                        messages.append(message)
                    else:
                        new_index.append(index)
                if values["category"] == "emerging_markets":
                    if index not in BAML_CATEGORIES.get("emerging_markets"):  # type: ignore
                        message = (
                            f"Invalid index, {index}, for category: 'emerging_markets'."
                            + f" Must be one of {', '.join(BAML_CATEGORIES.get('emerging_markets', ''))}."  # type: ignore
                        )
                        messages.append(message)
                    else:
                        new_index.append(index)
        if not new_index:
            raise OpenBBError(
                "No valid combinations of parameters were found."
                + f"\n{','.join(messages) if messages else ''}"
            )
        if messages:
            warn(",".join(messages))

        symbols: list = []
        if "yield_curve" in values["index"]:
            maturities_dict = BAML_CATEGORIES[values["category"]][values["index"]]  # type: ignore
            maturities = list(maturities_dict)
            symbols = [
                maturities_dict[item][values["index_type"]] for item in maturities
            ]
        else:
            items = (
                values["index"]
                if isinstance(values["index"], list)
                else values["index"].split(",")
            )
            symbols = [
                BAML_CATEGORIES[values["category"]].get(item, {}).get(values["index_type"])  # type: ignore
                for item in items
            ]
            symbols = [symbol for symbol in symbols if symbol]
        if not symbols:
            raise OpenBBError(
                "Error mapping the provided choices to series ID."
                + f"\n{','.join(messages) if messages else ''}"
            )
        values["index"] = ",".join(new_index)
        new_params = FredBondIndicesQueryParams(**values)
        new_params._symbols = ",".join(symbols)  # pylint: disable=protected-access

        return new_params