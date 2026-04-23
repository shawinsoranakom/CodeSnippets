def extract_data(  # noqa = PRL0912
        query: FinvizEquityScreenerQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract data from Finviz."""
        # pylint: disable=import-outside-toplevel
        import configparser  # noqa
        from finvizfinance import util
        from finvizfinance.screener import (
            financial,
            overview,
            ownership,
            performance,
            technical,
            valuation,
        )
        from numpy import nan
        from openbb_core.provider.utils.helpers import get_requests_session
        from openbb_finviz.utils.screener_helper import (
            get_preset_choices,
            d_check_screener,
            d_signals,
        )
        from pandas import DataFrame

        preset = None
        util.session = get_requests_session()

        try:
            data_dir = kwargs.get("preferences", {}).get("data_directory")
            preset_choices = get_preset_choices(data_dir)
            preset = query.preset
            if preset is not None and preset not in preset_choices:
                raise OpenBBError(
                    f"Invalid preset '{preset}'. Available presets are:\n{list(preset_choices)}"
                )
        except Exception as e:
            if preset is not None:
                raise e from e
            warn(f"Error loading presets -> {e.__class__.__name__}: {e}")
            preset = None

        data_type = query.metric
        ascend = False
        limit = query.limit
        sleep = 0.1  # For optimized pagination speed without creating too many requests error from Finviz.
        sort_by = "Change"
        df_screen = DataFrame()
        screen_type = {
            "overview": overview.Overview,
            "valuation": valuation.Valuation,
            "financial": financial.Financial,
            "ownership": ownership.Ownership,
            "performance": performance.Performance,
            "technical": technical.Technical,
        }

        if data_type in screen_type:
            screen = screen_type[data_type]()

        if preset is not None:
            preset_filter = configparser.RawConfigParser()
            preset_filter.optionxform = str  # type: ignore
            preset_filter.read(preset_choices[preset])
            d_general = preset_filter["General"]
            d_filters = {
                **preset_filter["Descriptive"],
                **preset_filter["Fundamental"],
                **preset_filter["Technical"],
            }
            for section in ["General", "Descriptive", "Fundamental", "Technical"]:
                for key, val in {**preset_filter[section]}.items():
                    if key not in d_check_screener:
                        raise OpenBBError(
                            f"The screener variable {section}.{key} shouldn't exist!\n"
                        )

                    if val not in d_check_screener[key]:
                        raise OpenBBError(
                            f"Invalid [{section}] {key}={val}. "
                            f"Choose one of the following options:\n{', '.join(d_check_screener[key])}.\n"
                        )

            d_filters = {k: v for k, v in d_filters.items() if v is not None}
            screen.set_filter(filters_dict=d_filters)
            asc = None

            asc = d_general.get("Ascend")

            if asc is not None:
                ascend = asc == "true"

            df_screen = screen.screener_view(
                order=d_general.get("Order", "Change"),
                limit=limit if limit else 100000,
                ascend=ascend,
                sleep_sec=sleep,
                verbose=0,
            )
        # If no preset is supplied, then set the filters based on the query parameters.
        else:
            if query.signal is not None:
                screen.set_filter(signal=d_signals[query.signal])
                if query.signal in ["unusual_volume", "most_active"]:
                    sort_by = "Relative Volume"
                elif query.signal == "top_losers":
                    ascend = True
                elif query.signal in ["new_low", "multiple_bottom", "double_bottom"]:
                    sort_by = "52-Week Low (Relative)"
                    ascend = True
                elif query.signal in ["new_high", "multiple_top", "double_top"]:
                    sort_by = "52-Week High (Relative)"
                elif query.signal == "oversold":
                    sort_by = "Relative Strength Index (14)"
                    ascend = True
                elif query.signal == "overbought":
                    sort_by = "Relative Strength Index (14)"
                elif query.signal == "most_volatile":
                    sort_by = "Volatility (Week)"
                else:
                    pass

            filters_dict: dict = {}

            if query.sector != "all":
                filters_dict["Sector"] = SECTOR_MAP[query.sector]

            if query.industry != "all":
                filters_dict["Industry"] = INDUSTRY_MAP[query.industry]  # type: ignore

            if query.exchange != "all":
                filters_dict["Exchange"] = EXCHANGE_MAP[query.exchange]

            if query.index != "all":
                filters_dict["Index"] = INDEX_MAP[query.index]

            if query.recommendation != "all":
                filters_dict["Analyst Recom."] = RECOMMENDATION_MAP[
                    query.recommendation
                ]

            if query.mktcap != "all":
                filters_dict["Market Cap."] = MARKET_CAP_MAP[query.mktcap]

            if query.filters_dict is not None:
                _filters_dict = query.filters_dict.copy()  # type: ignore
                order = _filters_dict.pop("Order", None)
                asc = _filters_dict.pop("Ascend", None)
                if asc:
                    ascend = asc == "true"
                if order:
                    sort_by = order
                filters_dict.update(_filters_dict)

            if filters_dict:
                screen.set_filter(filters_dict=filters_dict)

            if not filters_dict and query.signal is None:
                screen.set_filter(signal=d_signals["top_gainers"])
                warn(
                    "No filters or signal provided. Defaulting to 'top_gainers' signal."
                    + " Use the preset, 'all_stocks', to explicitly return every stock on Finviz."
                    + " Returning 10K symbols can take several minutes."
                )

            df_screen = screen.screener_view(
                order=sort_by,
                limit=limit if limit else 100000,
                ascend=ascend,
                sleep_sec=sleep,
                verbose=0,
            )

        if df_screen is None or df_screen.empty:
            raise EmptyDataError(
                "No tickers found for the supplied parameters. Try relaxing the constraints."
            )

        df_screen.columns = [val.strip("\n") for val in df_screen.columns]
        # Commas in the company name can cause issues with delimiters.
        if "Company" in df_screen.columns:
            df_screen["Company"] = df_screen["Company"].str.replace(",", "")

        return df_screen.convert_dtypes().replace({nan: None}).to_dict(orient="records")