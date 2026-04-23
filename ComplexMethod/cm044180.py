def plot_srlines(self, fig: OpenBBFigure, df_ta: pd.DataFrame):
        """Add support and resistance lines to plotly figure."""
        window = self.params["srlines"].get_argument_values("window")  # type: ignore
        window = window[0] if isinstance(window, list) and len(window) > 0 else 200

        def is_far_from_level(value, levels, df_stock):
            ave = np.mean(df_stock["high"] - df_stock["low"])
            return np.sum([abs(value - level) < ave for _, level in levels]) == 0

        def is_support(df, i):
            cond1 = df["low"][i] < df["low"][i - 1]
            cond2 = df["low"][i] < df["low"][i + 1]
            cond3 = df["low"][i + 1] < df["low"][i + 2]
            cond4 = df["low"][i - 1] < df["low"][i - 2]
            return cond1 and cond2 and cond3 and cond4

        def is_resistance(df, i):
            cond1 = df["high"][i] > df["high"][i - 1]
            cond2 = df["high"][i] > df["high"][i + 1]
            cond3 = df["high"][i + 1] > df["high"][i + 2]
            cond4 = df["high"][i - 1] > df["high"][i - 2]
            return cond1 and cond2 and cond3 and cond4

        df_ta2 = df_ta.copy()
        today = pd.to_datetime(datetime.now(), unit="ns")
        start_date = pd.to_datetime(datetime.now() - timedelta(days=window), unit="ns")

        df_ta2 = df_ta2.loc[(df_ta2.index >= start_date) & (df_ta2.index < today)]

        if df_ta2.index[-2].date() != df_ta2.index[-1].date():
            interval = 1440
        else:
            interval = (df_ta2.index[1] - df_ta2.index[0]).seconds / 60

        if interval <= 15:
            cut_days = 1 if interval < 15 else 2
            dt_unique_days = df_ta2.index.normalize().unique()  # type: ignore
            df_ta2 = df_ta2.loc[
                (df_ta2.index >= pd.to_datetime(dt_unique_days[-cut_days], unit="ns"))
                & (df_ta2.index < today)
            ].copy()

        levels: list = []
        x_range = df_ta2.index[-1].replace(hour=15, minute=59)
        if interval > 15:
            x_range = df_ta2.index[-1] + timedelta(days=15)
            if x_range.weekday() > 4:
                x_range = x_range + timedelta(days=7 - x_range.weekday())

        elif df_ta2.index[-1] >= today.replace(hour=15, minute=0):
            x_range = (df_ta2.index[-1] + timedelta(days=1)).replace(hour=11, minute=0)
            if x_range.weekday() > 4:
                x_range = x_range + timedelta(days=7 - x_range.weekday())

        for i in range(2, len(df_ta2) - 2):
            if is_support(df_ta2, i):
                lv = df_ta2["low"][i]
                if is_far_from_level(lv, levels, df_ta2):
                    levels.append((i, lv))
                    fig.add_scatter(
                        x=[df_ta.index[0], x_range],
                        y=[lv, lv],
                        opacity=0.8,
                        mode="lines+text",
                        text=["", f"{lv:{self.get_float_precision()}}"],
                        textposition="top center",
                        textfont=dict(
                            family="Arial Black", color="rgb(120, 70, 200)", size=10
                        ),
                        line=dict(
                            width=2, dash="dash", color="rgba(120, 70, 200, 0.70)"
                        ),
                        connectgaps=True,
                        showlegend=False,
                        row=1,
                        col=1,
                        secondary_y=False,
                    )
            elif is_resistance(df_ta2, i):
                lv = df_ta2["high"][i]
                if is_far_from_level(lv, levels, df_ta2):
                    levels.append((i, lv))
                    fig.add_scatter(
                        x=[df_ta.index[0], x_range],
                        y=[lv, lv],
                        opacity=0.85,
                        mode="lines+text",
                        text=["", f"{lv:{self.get_float_precision()}}"],
                        textposition="top center",
                        textfont=dict(
                            family="Arial Black", color="rgb(120, 70, 200)", size=10
                        ),
                        line=dict(
                            width=2, dash="dash", color="rgba(120, 70, 200, 0.70)"
                        ),
                        connectgaps=True,
                        showlegend=False,
                        row=1,
                        col=1,
                        secondary_y=False,
                    )

        return fig