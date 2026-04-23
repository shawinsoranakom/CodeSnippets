def wrap(
        self,
        console: "Console",
        width: int,
        *,
        justify: Optional["JustifyMethod"] = None,
        overflow: Optional["OverflowMethod"] = None,
        tab_size: int = 8,
        no_wrap: Optional[bool] = None,
    ) -> Lines:
        """Word wrap the text.

        Args:
            console (Console): Console instance.
            width (int): Number of cells available per line.
            justify (str, optional): Justify method: "default", "left", "center", "full", "right". Defaults to "default".
            overflow (str, optional): Overflow method: "crop", "fold", or "ellipsis". Defaults to None.
            tab_size (int, optional): Default tab size. Defaults to 8.
            no_wrap (bool, optional): Disable wrapping, Defaults to False.

        Returns:
            Lines: Number of lines.
        """
        wrap_justify = justify or self.justify or DEFAULT_JUSTIFY
        wrap_overflow = overflow or self.overflow or DEFAULT_OVERFLOW

        no_wrap = pick_bool(no_wrap, self.no_wrap, False) or overflow == "ignore"

        lines = Lines()
        for line in self.split(allow_blank=True):
            if "\t" in line:
                line.expand_tabs(tab_size)
            if no_wrap:
                if overflow == "ignore":
                    lines.append(line)
                    continue
                new_lines = Lines([line])
            else:
                offsets = divide_line(str(line), width, fold=wrap_overflow == "fold")
                new_lines = line.divide(offsets)
                for line in new_lines:
                    line.rstrip_end(width)
            if wrap_justify:
                new_lines.justify(
                    console, width, justify=wrap_justify, overflow=wrap_overflow
                )
            for line in new_lines:
                line.truncate(width, overflow=wrap_overflow)
            lines.extend(new_lines)
        return lines