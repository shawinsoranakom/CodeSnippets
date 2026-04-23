async def get_one(symbol):
            """Get data for one symbol."""
            ttm = f"{base_url}-ttm?symbol={symbol}&apikey={api_key}"
            limit = query.limit if query.ttm != "only" else 1
            metrics = f"{base_url}?symbol={symbol}&period={query.period}&limit={limit}&apikey={api_key}"
            result: list = []
            ttm_data = await get_data_many(ttm, **kwargs)
            metrics_data = await get_data_many(metrics, **kwargs)
            currency = None

            if metrics_data:
                if query.ttm != "only":
                    result.extend(metrics_data)
                currency = metrics_data[0].get("reportedCurrency")

            if ttm_data and query.ttm != "exclude":
                ttm_result = ttm_data[0]
                ttm_result["date"] = datetime.today().date().strftime("%Y-%m-%d")
                ttm_result["fiscal_period"] = "TTM"
                ttm_result["fiscal_year"] = datetime.today().year
                if currency:
                    ttm_result["reportedCurrency"] = currency
                result.insert(0, ttm_result)

            if not result:
                warnings.warn(f"Symbol Error: No data found for {symbol}.")

            if not result:
                warnings.warn(f"Symbol Error: No data found for {symbol}.")

            if result:
                results.extend(result)