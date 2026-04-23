def truncate(
        self,
        max_width: int,
        *,
        overflow: Optional["OverflowMethod"] = None,
        pad: bool = False,
    ) -> None:
        """Truncate text if it is longer that a given width.

        Args:
            max_width (int): Maximum number of characters in text.
            overflow (str, optional): Overflow method: "crop", "fold", or "ellipsis". Defaults to None, to use self.overflow.
            pad (bool, optional): Pad with spaces if the length is less than max_width. Defaults to False.
        """
        _overflow = overflow or self.overflow or DEFAULT_OVERFLOW
        if _overflow != "ignore":
            length = cell_len(self.plain)
            if length > max_width:
                if _overflow == "ellipsis":
                    self.plain = set_cell_size(self.plain, max_width - 1) + "…"
                else:
                    self.plain = set_cell_size(self.plain, max_width)
            if pad and length < max_width:
                spaces = max_width - length
                self._text = [f"{self.plain}{' ' * spaces}"]
                self._length = len(self.plain)