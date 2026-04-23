def buffer_with_style(
        self, width, quadsegs=8, end_cap_style=1, join_style=1, mitre_limit=5.0
    ):
        """
        Same as buffer() but allows customizing the style of the memoryview.

        End cap style can be round (1), flat (2), or square (3).
        Join style can be round (1), mitre (2), or bevel (3).
        Mitre ratio limit only affects mitered join style.
        """
        return self._topology(
            capi.geos_bufferwithstyle(
                self.ptr, width, quadsegs, end_cap_style, join_style, mitre_limit
            ),
        )