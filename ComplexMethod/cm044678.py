def write_styled(self, text: str, style: Style) -> None:
        """Write styled text to the terminal.

        Args:
            text (str): The text to write
            style (Style): The style of the text
        """
        color = style.color
        bgcolor = style.bgcolor
        if style.reverse:
            color, bgcolor = bgcolor, color

        if color:
            fore = color.downgrade(ColorSystem.WINDOWS).number
            fore = fore if fore is not None else 7  # Default to ANSI 7: White
            if style.bold:
                fore = fore | self.BRIGHT_BIT
            if style.dim:
                fore = fore & ~self.BRIGHT_BIT
            fore = self.ANSI_TO_WINDOWS[fore]
        else:
            fore = self._default_fore

        if bgcolor:
            back = bgcolor.downgrade(ColorSystem.WINDOWS).number
            back = back if back is not None else 0  # Default to ANSI 0: Black
            back = self.ANSI_TO_WINDOWS[back]
        else:
            back = self._default_back

        assert fore is not None
        assert back is not None

        SetConsoleTextAttribute(
            self._handle, attributes=ctypes.c_ushort(fore | (back << 4))
        )
        self.write_text(text)
        SetConsoleTextAttribute(self._handle, attributes=self._default_text)