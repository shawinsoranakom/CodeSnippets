def _get_stat(
        self,
        metric: Literal["open_interest", "volume", "DEX", "GEX"],
        moneyness: Literal["otm", "itm"] | None = None,
        date: str | None = None,
    ) -> dict:
        """Return the metric with keys: "total", "expiration", "strike".
        This method is not intended to be called directly.
        """
        # pylint: disable=import-outside-toplevel
        from numpy import inf, nan
        from pandas import DataFrame, concat

        df = self.dataframe

        if metric in ["DEX", "GEX"]:
            if not self.has_greeks:
                raise OpenBBError("Greeks were not found within the data.")
            df[metric] = abs(df[metric])

        total_calls = df[df.option_type == "call"][metric].sum()
        total_puts = df[df.option_type == "put"][metric].sum()
        total_metric = total_calls + total_puts
        total_metric_dict = {
            "Calls": total_calls,
            "Puts": total_puts,
            "Total": total_metric,
            "PCR": round(total_puts / total_calls, 4) if total_calls != 0 else 0,
        }

        df = DataFrame(df[df[metric].notnull()])  # type: ignore
        df["expiration"] = df.expiration.astype(str)

        if moneyness is not None:
            df_calls = DataFrame(
                df[df.strike >= df.underlying_price].query("option_type == 'call'")
                if moneyness == "otm"
                else df[df.strike <= df.underlying_price].query("option_type == 'call'")
            )
            df_puts = DataFrame(
                df[df.strike <= df.underlying_price].query("option_type == 'put'")
                if moneyness == "otm"
                else df[df.strike >= df.underlying_price].query("option_type == 'put'")
            )
            df = concat([df_calls, df_puts])

        if date is not None:
            date = self._get_nearest_expiration(date)
            df = DataFrame(df[df["expiration"].astype(str) == date])

        by_expiration = df.groupby("expiration")[[metric]].sum()[[metric]].copy()
        by_expiration = by_expiration.rename(columns={metric: "Total"})  # type: ignore
        by_expiration["Calls"] = df[df.option_type == "call"].groupby("expiration")[metric].sum().copy()  # type: ignore
        by_expiration["Puts"] = df[df.option_type == "put"].groupby("expiration")[metric].sum().copy()  # type: ignore
        by_expiration["PCR"] = round(by_expiration["Puts"] / by_expiration["Calls"], 4)
        by_expiration["Net Percent"] = round(
            (by_expiration["Total"] / total_metric) * 100, 4
        )
        by_expiration = (
            by_expiration[["Calls", "Puts", "Total", "Net Percent", "PCR"]]
            .replace({0: None, inf: None, nan: None})
            .dropna(how="all", axis=0)
        )
        by_expiration.index.name = "Expiration"
        by_expiration_dict = by_expiration.reset_index().to_dict(orient="records")
        by_strike = df.groupby("strike")[[metric]].sum()[[metric]].copy()
        by_strike = by_strike.rename(columns={metric: "Total"})  # type: ignore
        by_strike["Calls"] = df[df.option_type == "call"].groupby("strike")[metric].sum().copy()  # type: ignore
        by_strike["Puts"] = df[df.option_type == "put"].groupby("strike")[metric].sum().copy()  # type: ignore
        by_strike["PCR"] = round(by_strike["Puts"] / by_strike["Calls"], 4)
        by_strike["Net Percent"] = round((by_strike["Total"] / total_metric) * 100, 4)
        by_strike = (
            by_strike[["Calls", "Puts", "Total", "Net Percent", "PCR"]]
            .replace({0: None, inf: None, nan: None})
            .dropna(how="all", axis=0)
        )
        by_strike.index.name = "Strike"
        by_strike_dict = by_strike.reset_index().to_dict(orient="records")

        return {
            "total": total_metric_dict,
            "expiration": by_expiration_dict,
            "strike": by_strike_dict,
        }