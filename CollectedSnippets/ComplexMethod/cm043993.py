def transform_data(
        query: SAForwardSalesEstimatesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SAForwardSalesEstimatesData]:
        """Transform the data to the standard format."""
        tickers = query.symbol.split(",")  # type: ignore
        ids = data.get("ids", {})
        estimates = data.get("estimates", {})
        results: list[SAForwardSalesEstimatesData] = []
        for ticker in tickers:
            sa_id = str(ids.get(ticker, ""))
            if sa_id == "" or sa_id not in estimates:
                warn(f"Symbol Error: No data found for, {ticker}")
            seek_object = estimates.get(sa_id, {})
            if not seek_object:
                warn(f"No data found for {ticker}")
                continue
            items = len(seek_object.get("revenue_num_of_estimates"))
            if not items:
                warn(f"No data found for {ticker}")
                continue
            for i in range(0, items - 4):
                rev_estimates: dict = {}
                rev_estimates["symbol"] = ticker
                num_estimates = seek_object["revenue_num_of_estimates"].get(str(i))
                if not num_estimates:
                    continue
                period = num_estimates[0].get("period", {})
                if period:
                    period_type = period.get("periodtypeid")
                    rev_estimates["calendar_year"] = period.get("calendaryear")
                    rev_estimates["calendar_period"] = (
                        "Q" + str(period.get("calendarquarter", ""))
                        if period_type == "quarterly"
                        else "FY"
                    )
                    rev_estimates["date"] = period.get("periodenddate").split("T")[0]
                    rev_estimates["fiscal_year"] = period.get("fiscalyear")
                    rev_estimates["fiscal_period"] = (
                        "Q" + str(period.get("fiscalquarter", ""))
                        if period_type == "quarterly"
                        else "FY"
                    )
                rev_estimates["number_of_analysts"] = num_estimates[0].get(
                    "dataitemvalue"
                )
                mean = seek_object["revenue_consensus_mean"].get(str(i))
                if mean:
                    mean = mean[0].get("dataitemvalue")
                    rev_estimates["mean"] = int(float(mean))
                actual = (
                    seek_object["revenue_actual"][str(i)][0].get("dataitemvalue")
                    if i < 1
                    else None
                )
                if actual:
                    rev_estimates["actual"] = int(float(actual))
                low = seek_object["revenue_consensus_low"].get(str(i))
                if low:
                    low = low[0].get("dataitemvalue")
                    rev_estimates["low_estimate"] = int(float(low))
                high = seek_object["revenue_consensus_high"].get(str(i))
                if high:
                    high = high[0].get("dataitemvalue")
                    rev_estimates["high_estimate"] = int(float(high))
                # Calculate the estimated growth percent.
                this = float(mean) if mean else None
                prev = None
                percent = None
                try:
                    prev = float(
                        seek_object["revenue"][str(i - 1)][0].get("dataitemvalue")
                    )
                except KeyError:
                    prev = float(
                        seek_object["revenue_consensus_mean"][str(i - 1)][0].get(
                            "dataitemvalue"
                        )
                    )
                if this and prev:
                    percent = (this - prev) / prev
                rev_estimates["period_growth"] = percent
                results.append(
                    SAForwardSalesEstimatesData.model_validate(rev_estimates)
                )

        return results