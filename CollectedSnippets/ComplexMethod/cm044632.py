def _make_ansi_codes(self, color_system: ColorSystem) -> str:
        """Generate ANSI codes for this style.

        Args:
            color_system (ColorSystem): Color system.

        Returns:
            str: String containing codes.
        """

        if self._ansi is None:
            sgr: List[str] = []
            append = sgr.append
            _style_map = self._style_map
            attributes = self._attributes & self._set_attributes
            if attributes:
                if attributes & 1:
                    append(_style_map[0])
                if attributes & 2:
                    append(_style_map[1])
                if attributes & 4:
                    append(_style_map[2])
                if attributes & 8:
                    append(_style_map[3])
                if attributes & 0b0000111110000:
                    for bit in range(4, 9):
                        if attributes & (1 << bit):
                            append(_style_map[bit])
                if attributes & 0b1111000000000:
                    for bit in range(9, 13):
                        if attributes & (1 << bit):
                            append(_style_map[bit])
            if self._color is not None:
                sgr.extend(self._color.downgrade(color_system).get_ansi_codes())
            if self._bgcolor is not None:
                sgr.extend(
                    self._bgcolor.downgrade(color_system).get_ansi_codes(
                        foreground=False
                    )
                )
            self._ansi = ";".join(sgr)
        return self._ansi