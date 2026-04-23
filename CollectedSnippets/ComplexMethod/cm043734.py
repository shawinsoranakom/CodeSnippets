def _download_cover_page(
        self,
    ):  # pylint: disable=too-many-branches, too-many-statements, too-many-locals
        """Download the cover page table."""
        # pylint: disable=import-outside-toplevel
        from pandas import MultiIndex, to_datetime

        symbols_list: list = []
        try:
            response = self.download_file(self._cover_page_url, True, self._use_cache)
            if not response:
                raise RuntimeError("Failed to download cover page table")
            df = response[0]
            if isinstance(df.columns, MultiIndex):
                df = df.droplevel(0, axis=1)

            if df.empty or len(df) < 1:
                raise RuntimeError("Failed to read cover page table")

            fiscal_year = df[df.iloc[:, 0] == "Document Fiscal Year Focus"]

            if not fiscal_year.empty:
                fiscal_year = fiscal_year.iloc[:, 1].values[0]
            elif fiscal_year.empty:
                fiscal_year = None

            if fiscal_year:
                self._fiscal_year = fiscal_year

            fiscal_period = df[df.iloc[:, 0] == "Document Fiscal Period Focus"]

            if not fiscal_period.empty:
                fiscal_period = fiscal_period.iloc[:, 1].values[0]
            elif fiscal_period.empty:
                fiscal_period = None

            if fiscal_period:
                self._fiscal_period = fiscal_period

            title = (
                df.columns[0][0]
                if isinstance(df.columns, MultiIndex)
                else df.columns[0]
            )

            if title and "- shares" in title:
                shares_multiplier = title.split(" shares in ")[-1]
                multiplier = self._multiplier_map(shares_multiplier)
                shares_outstanding = (
                    df[df.iloc[:, 0].str.contains("Shares Outstanding")]
                    .iloc[:, 2]
                    .values[0]
                )
                as_of_date = (
                    df.columns[2][1]
                    if isinstance(df.columns, MultiIndex)
                    else df.columns[2]
                )

                if as_of_date and shares_outstanding:
                    self._shares_outstanding = {
                        to_datetime(as_of_date).strftime("%Y-%m-%d"): int(
                            shares_outstanding * multiplier
                        )
                    }

            if not df.empty:
                trading_symbols_df = df[
                    df.iloc[:, 0]
                    .astype(str)
                    .str.lower()
                    .isin(["trading symbol", "no trading symbol flag"])
                ]
                symbols_dict: dict = {}
                trading_symbols = (
                    trading_symbols_df.iloc[:, 1]
                    .str.strip()
                    .str.replace("true", "No Trading Symbol")
                    .tolist()
                )
                symbol_names = (
                    df[
                        df.iloc[:, 0].astype(str).str.strip()
                        == "Title of 12(b) Security"
                    ]
                    .iloc[:, 1]
                    .tolist()
                )
                exchange_names = (
                    df[
                        df.iloc[:, 0].astype(str).str.strip()
                        == "Security Exchange Name"
                    ]
                    .iloc[:, 1]
                    .fillna("No Exchange")
                    .tolist()
                )
                if trading_symbols:
                    self._trading_symbols = sorted(
                        [d for d in trading_symbols if d and d != "No Trading Symbol"]
                    )
                    symbols_dict = dict(zip(symbol_names, trading_symbols))
                    exchanges_dict = dict(zip(symbol_names, exchange_names))

                    for k, v in symbols_dict.items():
                        symbols_list.append(
                            {
                                "Title": k,
                                "Symbol": v,
                                "Exchange": exchanges_dict.get(k, "No Exchange"),
                            }
                        )

                df.columns = [d[1] if isinstance(d, tuple) else d for d in df.columns]
                df = df.iloc[:, :2].dropna(how="any")
                df.columns = ["key", "value"]
                output = df.set_index("key").to_dict()["value"]

                if not output.get("SIC") and self._sic:
                    output["SIC"] = self._sic
                    output["SIC Organization Name"] = self.sic_organization_name

                for k, v in output.copy().items():
                    if k in [
                        "Title of 12(b) Security",
                        "Trading Symbol",
                        "Security Exchange Name",
                        "No Trading Symbol Flag",
                    ]:
                        del output[k]

                if symbols_list:
                    output["12(b) Securities"] = symbols_list

                self._cover_page = output

        except IndexError:
            pass

        except Exception as e:
            raise RuntimeError(
                f"Failed to download and read the cover page table: {e}"
            ) from e