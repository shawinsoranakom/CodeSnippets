def transform_data(
        query: DeribitFuturesCurveQueryParams, data: list, **kwargs: Any
    ) -> list[DeribitFuturesCurveData]:
        """Transform the data."""
        # pylint: disable=import-outside-toplevel
        from datetime import datetime  # noqa
        from pandas import to_datetime

        if not data:
            raise EmptyDataError("No data found")

        futures_curve: list[DeribitFuturesCurveData] = []

        for d in data:
            if not d:
                continue

            ins_name = d.get("instrument_name", "")
            exp = ins_name.split("-")[1]
            hours_ago = d.get("hours_ago", 0)
            exp = (
                datetime.today().strftime("%Y-%m-%d")
                if exp == "PERPETUAL"
                else to_datetime(exp).strftime("%Y-%m-%d")
            )

            price = d.get("last_price", d.get("mark_price"))

            result = {"expiration": exp, "price": price}
            if query.hours_ago:
                result["hours_ago"] = hours_ago

            if price:
                futures_curve.append(DeribitFuturesCurveData.model_validate(result))

        if not futures_curve:
            raise EmptyDataError("No data found.")

        return sorted(futures_curve, key=lambda x: x.expiration)