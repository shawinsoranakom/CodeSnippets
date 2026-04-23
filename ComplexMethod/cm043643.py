def get_one(symbol) -> dict:
            """Get the data for one symbol."""
            result: dict = {}
            try:
                data = finvizfinance(symbol)
                fundament = data.ticker_fundament()
                mkt_cap = (
                    fundament.get("Market Cap", None)
                    if fundament.get("Market Cap", "-") != "-"
                    else None
                )
                if mkt_cap:
                    mkt_cap = float(
                        str(mkt_cap)
                        .replace("B", "e+9")
                        .replace("M", "e+6")
                        .replace("K", "e+3")
                    )
            except Exception as e:  # pylint: disable=W0718
                warn(f"Failed to get data for {symbol} -> {e}")
                return result
            result.update(
                {
                    "symbol": symbol,
                    "market_cap": int(mkt_cap) if mkt_cap is not None else None,
                    "pe_ratio": (
                        fundament.get("P/E", None)
                        if fundament.get("P/E", "-") != "-"
                        else None
                    ),
                    "eps": (
                        fundament.get("EPS (ttm)", None)
                        if fundament.get("EPS (ttm)", "-") != "-"
                        else None
                    ),
                    "forward_pe": (
                        fundament.get("Forward P/E", None)
                        if fundament.get("Forward P/E", "-") != "-"
                        else None
                    ),
                    "price_to_sales": (
                        fundament.get("P/S", None)
                        if fundament.get("P/S", "-") != "-"
                        else None
                    ),
                    "price_to_book": (
                        fundament.get("P/B", None)
                        if fundament.get("P/B", "-") != "-"
                        else None
                    ),
                    "book_value_per_share": (
                        fundament.get("Book/sh", None)
                        if fundament.get("Book/sh", "-") != "-"
                        else None
                    ),
                    "price_to_cash": (
                        fundament.get("P/C", None)
                        if fundament.get("P/C", "-") != "-"
                        else None
                    ),
                    "cash_per_share": (
                        fundament.get("Cash/sh", None)
                        if fundament.get("Cash/sh", "-") != "-"
                        else None
                    ),
                    "price_to_free_cash_flow": (
                        fundament.get("P/FCF", None)
                        if fundament.get("P/FCF", "-") != "-"
                        else None
                    ),
                    "debt_to_equity": (
                        fundament.get("Debt/Eq", None)
                        if fundament.get("Debt/Eq", "-") != "-"
                        else None
                    ),
                    "long_term_debt_to_equity": (
                        fundament.get("LT Debt/Eq", None)
                        if fundament.get("LT Debt/Eq", "-") != "-"
                        else None
                    ),
                    "quick_ratio": (
                        fundament.get("Quick Ratio", None)
                        if fundament.get("Quick Ratio", "-") != "-"
                        else None
                    ),
                    "current_ratio": (
                        fundament.get("Current Ratio", None)
                        if fundament.get("Current Ratio", "-") != "-"
                        else None
                    ),
                    "gross_margin": (
                        float(str(fundament.get("Gross Margin", None)).replace("%", ""))
                        / 100
                        if fundament.get("Gross Margin", "-") != "-"
                        else None
                    ),
                    "profit_margin": (
                        float(
                            str(fundament.get("Profit Margin", None)).replace("%", "")
                        )
                        / 100
                        if fundament.get("Profit Margin", "-") != "-"
                        else None
                    ),
                    "operating_margin": (
                        float(str(fundament.get("Oper. Margin", None)).replace("%", ""))
                        / 100
                        if fundament.get("Oper. Margin", "-") != "-"
                        else None
                    ),
                    "return_on_assets": (
                        float(str(fundament.get("ROA", None)).replace("%", "")) / 100
                        if fundament.get("ROA", "-") != "-"
                        else None
                    ),
                    "return_on_investment": (
                        float(str(fundament.get("ROI", None)).replace("%", "")) / 100
                        if fundament.get("ROI", "-") != "-"
                        else None
                    ),
                    "return_on_equity": (
                        float(str(fundament.get("ROE", None)).replace("%", "")) / 100
                        if fundament.get("ROE", "-") != "-"
                        else None
                    ),
                    "payout_ratio": (
                        float(str(fundament.get("Payout", None)).replace("%", "")) / 100
                        if fundament.get("Payout", "-") != "-"
                        else None
                    ),
                    "dividend_yield": (
                        float(str(fundament.get("Dividend %", None)).replace("%", ""))
                        / 100
                        if fundament.get("Dividend %", "-") != "-"
                        else None
                    ),
                }
            )

            return result