def split_lines(cls, segments: Iterable["Segment"]) -> Iterable[List["Segment"]]:
        """Split a sequence of segments in to a list of lines.

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
                        yield line
                        line = []
                        append = line.append
            else:
                append(segment)
        if line:
            yield line