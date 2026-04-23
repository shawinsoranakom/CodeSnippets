def _invoke(self, **kwargs):
        if self.check_if_canceled("YahooFinance processing"):
            return None

        if not kwargs.get("stock_code"):
            self.set_output("report", "")
            return ""

        last_e = ""
        for _ in range(self._param.max_retries+1):
            if self.check_if_canceled("YahooFinance processing"):
                return None

            yahoo_res = []
            try:
                msft = yf.Ticker(kwargs["stock_code"])
                if self.check_if_canceled("YahooFinance processing"):
                    return None

                if self._param.info:
                    yahoo_res.append("# Information:\n" + pd.Series(msft.info).to_markdown() + "\n")
                if self._param.history:
                    yahoo_res.append("# History:\n" + msft.history().to_markdown() + "\n")
                if self._param.financials:
                    yahoo_res.append("# Calendar:\n" + pd.DataFrame(msft.calendar).to_markdown() + "\n")
                if self._param.balance_sheet:
                    yahoo_res.append("# Balance sheet:\n" + msft.balance_sheet.to_markdown() + "\n")
                    yahoo_res.append("# Quarterly balance sheet:\n" + msft.quarterly_balance_sheet.to_markdown() + "\n")
                if self._param.cash_flow_statement:
                    yahoo_res.append("# Cash flow statement:\n" + msft.cashflow.to_markdown() + "\n")
                    yahoo_res.append("# Quarterly cash flow statement:\n" + msft.quarterly_cashflow.to_markdown() + "\n")
                if self._param.news:
                    yahoo_res.append("# News:\n" + pd.DataFrame(msft.news).to_markdown() + "\n")
                self.set_output("report", "\n\n".join(yahoo_res))
                return self.output("report")
            except Exception as e:
                if self.check_if_canceled("YahooFinance processing"):
                    return None

                last_e = e
                logging.exception(f"YahooFinance error: {e}")
                time.sleep(self._param.delay_after_error)

        if last_e:
            self.set_output("_ERROR", str(last_e))
            return f"YahooFinance error: {last_e}"

        assert False, self.output()