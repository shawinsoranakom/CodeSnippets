def transform_data(
        query: TmxInsiderTradingQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[TmxInsiderTradingData]:
        """Transform the data."""
        data = data.copy()
        results = []
        flattened_insiders = []
        for activity in data["insiderActivities"]:  # type: ignore
            for transaction_type in ["buy", "sell"]:
                for transaction in activity[transaction_type]:
                    new_transaction = {
                        "period": activity["periodkey"],
                        "acquisition_or_disposition": transaction_type,
                        "owner_name": transaction["name"],
                        "number_of_trades": transaction["trades"],
                        "securities_transacted": transaction["shares"],
                        "securities_owned": transaction["sharesHeld"],
                        "trade_value": transaction["tradeValue"],
                    }
                    flattened_insiders.append(new_transaction)
        flattened_summary = []
        for activity in data["activitySummary"]:  # type: ignore
            new_activity = {
                "period": activity["periodkey"],
                "securities_bought": activity["buyShares"],
                "securities_sold": activity["soldShares"],
                "net_activity": activity["netActivity"],
                "securities_transacted": activity["totalShares"],
            }
            flattened_summary.append(new_activity)
        if query.summary is False and len(flattened_insiders) > 0:
            results = flattened_insiders
        elif query.summary is True and len(flattened_summary) > 0:
            results = flattened_summary

        return [TmxInsiderTradingData.model_validate(d) for d in results]