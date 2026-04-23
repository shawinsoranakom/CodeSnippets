def get_one(symbol) -> dict:
            """Get the data for one symbol."""
            result: dict = {}
            try:
                data = finvizfinance(symbol)
                fundament = data.ticker_fundament()
                description = data.ticker_description()
            except Exception as e:  # pylint: disable=W0718
                messages.append(f"Failed to get data for {symbol} -> {e}")
                return result
            div_yield = (
                float(str(fundament.get("Dividend %", None)).replace("%", "")) / 100
                if fundament.get("Dividend %", "-") != "-"
                else None
            )
            inst_own = (
                float(str(fundament.get("Inst Own", None)).replace("%", "")) / 100
                if fundament.get("Inst Own", "-") != "-"
                else None
            )
            result.update(
                {
                    "symbol": symbol,
                    "exchange": (
                        fundament.get("Exchange", None)
                        if fundament.get("Exchange", "-") != "-"
                        else None
                    ),
                    "name": (
                        fundament.get("Company", None)
                        if fundament.get("Company", "-") != "-"
                        else None
                    ),
                    "sector": (
                        fundament.get("Sector", None)
                        if fundament.get("Sector", "-") != "-"
                        else None
                    ),
                    "industry_category": (
                        fundament.get("Industry", None)
                        if fundament.get("Industry", "-") != "-"
                        else None
                    ),
                    "hq_country": (
                        fundament.get("Country", None)
                        if fundament.get("Country", "-") != "-"
                        else None
                    ),
                    "employees": (
                        fundament.get("Employees", None)
                        if fundament.get("Employees", "-") != "-"
                        else None
                    ),
                    "index": (
                        fundament.get("Index", None)
                        if fundament.get("Index", "-") != "-"
                        else None
                    ),
                    "beta": (
                        fundament.get("Beta", None)
                        if fundament.get("Beta", "-") != "-"
                        else None
                    ),
                    "optionable": (
                        fundament.get("Optionable", None)
                        if fundament.get("Optionable", "-") != "-"
                        else None
                    ),
                    "shortable": (
                        fundament.get("Shortable", None)
                        if fundament.get("Shortable", "-") != "-"
                        else None
                    ),
                    "shares_outstanding": (
                        fundament.get("Shs Outstand", None)
                        if fundament.get("Shs Outstand", "-") != "-"
                        else None
                    ),
                    "shares_float": (
                        fundament.get("Shs Float", None)
                        if fundament.get("Shs Float", "-") != "-"
                        else None
                    ),
                    "short_interest": (
                        fundament.get("Short Interest", None)
                        if fundament.get("Short Interest", "-") != "-"
                        else None
                    ),
                    "institutional_ownership": inst_own if inst_own else None,
                    "market_cap": (
                        fundament.get("Market Cap", None)
                        if fundament.get("Market Cap", "-") != "-"
                        else None
                    ),
                    "dividend_yield": div_yield if div_yield else None,
                    "earnings_date": (
                        fundament.get("Earnings", None)
                        if fundament.get("Earnings", "-") != "-"
                        else None
                    ),
                    "long_description": description if description else None,
                }
            )

            return result