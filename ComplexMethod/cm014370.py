def __init__(
        self,
        grouped_results: list[tuple[common.Measurement | None, ...]],
        time_scale: float,
        time_unit: str,
        trim_significant_figures: bool,
        highlight_warnings: bool,
    ) -> None:
        self._grouped_results = grouped_results
        self._flat_results = [*it.chain.from_iterable(grouped_results)]
        self._time_scale = time_scale
        self._time_unit = time_unit
        self._trim_significant_figures = trim_significant_figures
        self._highlight_warnings = (
            highlight_warnings
            and any(r.has_warnings for r in self._flat_results if r)
        )
        leading_digits = [
            int(_tensor(r.median / self._time_scale).log10().ceil()) if r else None
            for r in self._flat_results
        ]
        unit_digits = max(d for d in leading_digits if d is not None)
        decimal_digits = min(
            max(m.significant_figures - digits, 0)
            for digits, m in zip(leading_digits, self._flat_results, strict=True)
            if (m is not None) and (digits is not None)
        ) if self._trim_significant_figures else 1
        length = unit_digits + decimal_digits + (1 if decimal_digits else 0)
        self._template = f"{{:>{length}.{decimal_digits}f}}{{:>{7 if self._highlight_warnings else 0}}}"