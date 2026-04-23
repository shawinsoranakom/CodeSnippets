def _chart(
        cls,
        obbject: OBBject,
        **kwargs,
    ) -> None:
        """Create a chart from the command output."""
        try:
            if "charting" not in obbject.accessors:
                raise OpenBBError(
                    "Charting is not installed. Please install `openbb-charting`."
                )
            # Here we will pop the chart_params kwargs and flatten them into the kwargs.
            chart_params = {}
            extra_params = getattr(obbject, "_extra_params", {})

            if extra_params and "chart_params" in extra_params:
                chart_params = extra_params.get("chart_params", {})

            if kwargs.get("chart_params"):
                chart_params.update(kwargs.pop("chart_params", {}))
            # Verify that kwargs is not nested as kwargs so we don't miss any chart params.
            if (
                "kwargs" in kwargs
                and "chart_params" in kwargs["kwargs"]
                and kwargs["kwargs"].get("chart_params")
            ):
                chart_params.update(kwargs.pop("kwargs", {}).get("chart_params", {}))

            if chart_params:
                kwargs.update(chart_params)

            obbject.charting.show(render=False, **kwargs)  # type: ignore[attr-defined]
        except Exception as e:  # pylint: disable=broad-exception-caught
            if Env().DEBUG_MODE:
                raise OpenBBError(e) from e
            warn(str(e), OpenBBWarning)