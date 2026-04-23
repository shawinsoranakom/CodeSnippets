def decode_line(self, line: str) -> Text:
        """Decode a line containing ansi codes.

        Args:
            line (str): A line of terminal output.

        Returns:
            Text: A Text instance marked up according to ansi codes.
        """
        from_ansi = Color.from_ansi
        from_rgb = Color.from_rgb
        _Style = Style
        text = Text()
        append = text.append
        line = line.rsplit("\r", 1)[-1]
        for plain_text, sgr, osc in _ansi_tokenize(line):
            if plain_text:
                append(plain_text, self.style or None)
            elif osc is not None:
                if osc.startswith("8;"):
                    _params, semicolon, link = osc[2:].partition(";")
                    if semicolon:
                        self.style = self.style.update_link(link or None)
            elif sgr is not None:
                # Translate in to semi-colon separated codes
                # Ignore invalid codes, because we want to be lenient
                codes = [
                    min(255, int(_code) if _code else 0)
                    for _code in sgr.split(";")
                    if _code.isdigit() or _code == ""
                ]
                iter_codes = iter(codes)
                for code in iter_codes:
                    if code == 0:
                        # reset
                        self.style = _Style.null()
                    elif code in SGR_STYLE_MAP:
                        # styles
                        self.style += _Style.parse(SGR_STYLE_MAP[code])
                    elif code == 38:
                        #  Foreground
                        with suppress(StopIteration):
                            color_type = next(iter_codes)
                            if color_type == 5:
                                self.style += _Style.from_color(
                                    from_ansi(next(iter_codes))
                                )
                            elif color_type == 2:
                                self.style += _Style.from_color(
                                    from_rgb(
                                        next(iter_codes),
                                        next(iter_codes),
                                        next(iter_codes),
                                    )
                                )
                    elif code == 48:
                        # Background
                        with suppress(StopIteration):
                            color_type = next(iter_codes)
                            if color_type == 5:
                                self.style += _Style.from_color(
                                    None, from_ansi(next(iter_codes))
                                )
                            elif color_type == 2:
                                self.style += _Style.from_color(
                                    None,
                                    from_rgb(
                                        next(iter_codes),
                                        next(iter_codes),
                                        next(iter_codes),
                                    ),
                                )

        return text