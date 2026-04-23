def show(self, render: bool = True, **kwargs):
        """Display chart and save it to the OBBject."""
        # pylint: disable=import-outside-toplevel
        from openbb_charting.core.openbb_figure import OpenBBFigure

        try:
            charting_function = self._get_chart_function(
                self._obbject._route or ""  # pylint: disable=protected-access
            )
            kwargs["obbject_item"] = self._obbject.results
            kwargs["charting_settings"] = self._charting_settings
            kwargs["standard_params"] = (
                self._obbject._standard_params  # pylint: disable=protected-access
            )
            # If the provider interface isn't used, endpoint kwargs are already here.
            # Don't overwrite them.
            obb_kwargs = (
                self._obbject._extra_params or {}  # pylint: disable=protected-access
            )
            if obb_kwargs:
                for k, v in obb_kwargs.items():
                    kwargs["extra_params"].update({k: v})

            kwargs["provider"] = self._obbject.provider
            kwargs["extra"] = self._obbject.extra
            kwargs.setdefault(
                "command_location",
                self._obbject._route or "",  # pylint: disable=protected-access
            )

            # Handle different types of output from the charting endpoint.
            chart_response: Any = charting_function(**kwargs)

            # If returned a Chart object, set as-is.
            if isinstance(chart_response, Chart):
                self._obbject.chart = chart_response
            # If just an OpenBBFigure gets returned, create the serialized version for the API.
            elif isinstance(chart_response, OpenBBFigure):
                fig = chart_response
                content = fig.show(external=True, **kwargs).to_plotly_json()
                self._obbject.chart = Chart(
                    fig=fig, content=content, format=self._format
                )
            # Current functions return this.
            elif isinstance(chart_response, tuple) and len(chart_response) == 2:
                fig, content = chart_response

                if isinstance(fig, OpenBBFigure):
                    content = fig.show(external=True, **kwargs).to_plotly_json()  # type: ignore
                    self._obbject.chart = Chart(
                        fig=fig, content=content, format=self._format
                    )
                else:
                    self._obbject.chart = Chart(
                        fig=fig, content=content, format=type(fig).__name__
                    )

            else:
                self._obbject.chart = Chart(
                    fig=chart_response, content=None, format="unknown"
                )

            if render and hasattr(fig, "show"):
                fig.show(**kwargs)

        except (RuntimeError, OpenBBError) as e:
            raise e from e

        except Exception:  # pylint: disable=W0718
            try:
                fig = self.create_line_chart(data=self._obbject.results, render=False, **kwargs)  # type: ignore
                fig = self._set_chart_style(fig)  # type: ignore
                content = fig.show(external=True, **kwargs).to_plotly_json()  # type: ignore
                self._obbject.chart = Chart(
                    fig=fig, content=content, format=self._format
                )
                if render:
                    fig.show(**kwargs)  # type: ignore
            except Exception as e:
                raise RuntimeError(
                    "Failed to automatically create a generic chart with the data provided."
                    + f" -> {e} -> {e.args}"
                ) from e