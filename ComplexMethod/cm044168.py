def _add_cmd_source(self, command_location: str | None = "") -> None:
        """Set the watermark for OpenBB Terminal."""
        if command_location:
            yaxis = self.layout.yaxis
            yaxis2 = self.layout.yaxis2 if hasattr(self.layout, "yaxis2") else None
            xshift = -70 if yaxis.side == "right" else -80

            if self.layout.margin["l"] > 100:
                xshift -= 50 if self._added_logscale else 40

            if (
                yaxis2
                and (yaxis.title.text and yaxis2.title.text)
                and (yaxis.side == "left" or yaxis2.side == "left")
            ):
                self.layout.margin["l"] += 20

            if (yaxis2 and yaxis2.side == "left") or yaxis.side == "left":
                title = (
                    yaxis.title.text
                    if not yaxis2 or yaxis2.side != "left"
                    else yaxis2.title.text
                )
                xshift = -110 if not title else -135
                self.layout.margin["l"] += 60

            self.add_annotation(
                x=0,
                y=0.5,
                yref="paper",
                xref="paper",
                text=command_location,
                textangle=-90,
                font_size=24,
                font_color="gray" if self._theme.mapbox_style == "dark" else "black",
                opacity=0.5,
                yanchor="middle",
                xanchor="left",
                xshift=xshift + self.cmd_xshift,
            )