def __init__(  # pylint: disable=R0917
        self,
        data: Union[list[Data], "DataFrame"],
        benchmark: str,
        study: Literal["price", "volume", "volatility"] | None = "price",
        long_period: int | None = 252,
        short_period: int | None = 21,
        window: int | None = 21,
        trading_periods: int | None = 252,
    ):
        """Initialize the class."""
        # pylint: disable=import-outside-toplevel
        import contextlib  # noqa
        from openbb_core.app.model.obbject import OBBject  # noqa
        from openbb_core.app.utils import (  # noqa
            basemodel_to_df,
            convert_to_basemodel,
            df_to_basemodel,
        )
        from pandas import DataFrame  # noqa

        benchmark = benchmark.upper()
        df = DataFrame()

        target_col = "volume" if study == "volume" else "close"

        if isinstance(data, OBBject):
            data = data.results  # type: ignore

        if isinstance(data, list) and (
            all(isinstance(d, Data) for d in data)
            or all(isinstance(d, dict) for d in data)
        ):
            with contextlib.suppress(Exception):
                df = basemodel_to_df(convert_to_basemodel(data), index="date")

        if isinstance(data, DataFrame) and not df.empty:
            df = data.copy()
            if "date" in df.columns:
                df.set_index("date", inplace=True)

        if df.empty:
            raise ValueError(
                "Data must be a list of Data objects or a DataFrame with a 'date' column."
            )

        if "symbol" in df.columns:
            df = df.pivot(columns="symbol", values=target_col)

        if benchmark not in df.columns:
            raise RuntimeError("The benchmark symbol was not found in the data.")

        benchmark_data = df.pop(benchmark).to_frame()
        symbols_data = df

        if len(symbols_data) <= 252 and study in ["price", "volume"]:  # type: ignore
            raise ValueError(
                "Supplied data must be daily intervals and have more than one year of back data to calculate"
                " the most recent day in the time series."
            )

        if study == "volatility" and len(symbols_data) <= 504:  # type: ignore
            raise ValueError(
                "Supplied data must be daily intervals and have more than two years of back data to calculate"
                " the most recent day in the time series as a volatility study."
            )
        self.symbols = df.columns.to_list()
        self.benchmark = benchmark
        self.study = study
        self.long_period = long_period
        self.short_period = short_period
        self.window = window
        self.trading_periods = trading_periods
        self.symbols_data = symbols_data  # type: ignore
        self.benchmark_data = benchmark_data  # type: ignore
        self._process_data()  # type: ignore
        self.symbols_data = df_to_basemodel(self.symbols_data.reset_index())  # type: ignore
        self.benchmark_data = df_to_basemodel(self.benchmark_data.reset_index())