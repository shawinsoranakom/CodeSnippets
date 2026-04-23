def split_lines_terminator(
        cls, segments: Iterable["Segment"]
    ) -> Iterable[Tuple[List["Segment"], bool]]:
        """Split a sequence of segments in to a list of lines and a boolean to indicate if there was a new line.

        Args:
            segments (Iterable[Segment]): Segments potentially containing line feeds.

        Yields:
            Iterable[List[Segment]]: Iterable of segment lists, one per line.
        """
        line: List[Segment] = []
        append = line.append

        for segment in segments:
            if "\n" in segment.text and not segment.control:
                text, style, _ = segment
                while text:
                    _text, new_line, text = text.partition("\n")
                    if _text:
                        append(cls(_text, style))
                    if new_line:
                        yield (line, True)
                        line = []
                        append = line.append
            else:
                append(segment)
        if line:
            yield (line, False)