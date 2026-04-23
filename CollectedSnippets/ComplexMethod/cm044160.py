def apply_style(self, style: str | None = "") -> None:
        """Apply the style to the libraries."""
        style = style or self.plt_style

        if style != self.plt_style:
            self.load_style(style)

        style = style.lower().replace("light", "white")  # type: ignore

        if self.plt_style and self.plotly_template:
            self.plotly_template.setdefault("layout", {}).setdefault(
                "mapbox", {}
            ).setdefault("style", "dark")
            if "tables" in self.plt_styles_available:
                tables = self.load_json_style(self.plt_styles_available["tables"])
                pio.templates["openbb_tables"] = go.layout.Template(tables)
            try:
                pio.templates["openbb"] = go.layout.Template(self.plotly_template)
            except ValueError as err:
                if "plotly.graph_objs.Layout: 'legend2'" in str(err):
                    warn(
                        "[red]Warning: Plotly multiple legends are "
                        "not supported in currently installed version.[/]\n\n"
                        "[yellow]Please update plotly to version >= 5.15.0[/]\n"
                        "[green]pip install plotly --upgrade[/]"
                    )
                    sys.exit(1)

            if style in ["dark", "white"]:
                pio.templates.default = f"plotly_{style}+openbb"
                return

            pio.templates.default = "openbb"
            self.mapbox_style = (
                self.plotly_template.setdefault("layout", {})
                .setdefault("mapbox", {})
                .setdefault("style", "dark")
            )