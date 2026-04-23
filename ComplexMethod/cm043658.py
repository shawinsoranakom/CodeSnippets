def transform_data(
        query: IntrinioEtfHoldingsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[IntrinioEtfHoldingsData]:
        """Transform data."""
        if not data or isinstance(data, dict) and data.get("error"):
            if isinstance(data, list) and data == []:
                raise OpenBBError(
                    str(
                        f"No holdings were found for {query.symbol}, and the response from Intrinio was empty."
                    )
                )
            raise OpenBBError(str(f"{data.get('message')} {query.symbol}: {data['error']}"))  # type: ignore

        results: list[IntrinioEtfHoldingsData] = []
        for d in sorted(data, key=lambda x: x["weighting"], reverse=True):
            # This field is deprecated and is dupilcated in the response.
            _ = d.pop("composite_figi", None)
            if d.get("coupon"):
                d["coupon"] = d["coupon"] / 100
            results.append(IntrinioEtfHoldingsData.model_validate(d))

        return results