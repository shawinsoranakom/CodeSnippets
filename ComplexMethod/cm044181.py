def plot_fib(self, fig: OpenBBFigure, df_ta: pd.DataFrame):
        """Add fibonacci to plotly figure."""
        try:
            from openbb_technical.helpers import (  # pylint: disable=import-outside-toplevel
                calculate_fib_levels,
            )
        except ImportError:
            warnings.warn(
                "In order to use the Fibonacci indicator in your plot,"
                " you need to install the `openbb-technical` package."
            )
            return fig

        limit = self.params["fib"].get_argument_values("limit") or 120  # type: ignore
        start_date = self.params["fib"].get_argument_values("start_date") or None  # type: ignore
        end_date = self.params["fib"].get_argument_values("end_date") or None  # type: ignore
        close = self.params["fib"].get_argument_values("close") or "close"  # type: ignore
        (
            df_fib,
            min_date,
            max_date,
            min_pr,
            max_pr,
            lvl_text,
        ) = calculate_fib_levels(
            df_ta,
            close,
            limit,
            start_date,
            end_date,  # type: ignore
        )
        levels = df_fib.Price
        fibs = [
            "<b>0</b>",
            "<b>0.235</b>",
            "<b>0.382</b>",
            "<b>0.5</b>",
            "<b>0.618</b>",
            "<b>0.65</b>",
            "<b>1</b>",
        ]
        min_date = pd.to_datetime(min_date).to_pydatetime()
        max_date = pd.to_datetime(max_date).to_pydatetime()
        self.df_fib = df_fib  # pylint: disable=attribute-defined-outside-init

        fig.add_scatter(
            x=[min_date, max_date],
            y=[min_pr, max_pr],
            opacity=0.85,
            mode="lines",
            connectgaps=True,
            line=PLT_FIB_COLORWAY[8],
            showlegend=False,
            row=1,
            col=1,
            secondary_y=False,
        )
        df_ta2 = df_ta.copy()
        interval = 1440
        if df_ta2.index[-2].date() == df_ta2.index[-1].date():
            interval = (df_ta2.index[1] - df_ta2.index[0]).seconds / 60
            dt_unique_days = df_ta2.index.normalize().unique()  # type: ignore

            if interval not in [15, 30, 60] and len(dt_unique_days) <= 3:
                df_ta2 = df_ta2.loc[
                    (df_ta2.index >= dt_unique_days[-1])
                    & (df_ta2.index < datetime.now())
                ].copy()
                df_ta2 = df_ta2.between_time("09:30", "20:00").copy()

        for i in range(7):
            idx_int = 4 if lvl_text == "left" else 5
            text_pos = f"bottom {lvl_text}" if i != idx_int else f"top {lvl_text}"

            if fibs[i] == "<b>0</b>":
                text_pos = (
                    f"top {lvl_text}" if lvl_text != "right" else f"bottom {lvl_text}"
                )
            text = ["", f"<b>{fibs[i]} ({levels[i]:{self.get_float_precision()}})</b>"]
            if lvl_text == "right":
                text = [text[1], text[0]]

            fig.add_scatter(
                name=fibs[i],
                x=[min_date, df_ta2.index.max()],
                y=[levels[i], levels[i]],
                opacity=0.85,
                mode="lines+text",
                text=text,
                textposition=text_pos,
                textfont=dict(PLT_FIB_COLORWAY[7], color=PLT_FIB_COLORWAY[i]),
                line_color=PLT_FIB_COLORWAY[i],
                line_width=1.5,
                showlegend=False,
                row=1,
                col=1,
                secondary_y=False,
            )

        return fig