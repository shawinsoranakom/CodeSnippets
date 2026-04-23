def production_definitions(
        self, lines: Iterable[str], /
    ) -> Iterator[tuple[str, list[tuple[str, str]]]]:
        """Yield pairs of rawsource and production content dicts."""
        production_lines: list[str] = []
        production_content: list[tuple[str, str]] = []
        for line in lines:
            # If this line is the start of a new rule (text in the column 1),
            # emit the current production and start a new one.
            if not line[:1].isspace():
                rawsource = '\n'.join(production_lines)
                production_lines.clear()
                if production_content:
                    yield rawsource, production_content
                    production_content = []

            # Append the current line for the raw source
            production_lines.append(line)

            # Parse the line into constituent parts
            last_pos = 0
            for match in self.grammar_re.finditer(line):
                # Handle text between matches
                if match.start() > last_pos:
                    unmatched_text = line[last_pos : match.start()]
                    production_content.append(('text', unmatched_text))
                last_pos = match.end()

                # Handle matches.
                # After filtering None (non-matches), exactly one groupdict()
                # entry should remain.
                [(re_group_name, content)] = (
                    (re_group_name, content)
                    for re_group_name, content in match.groupdict().items()
                    if content is not None
                )
                production_content.append((re_group_name, content))
            production_content.append(('text', line[last_pos:] + '\n'))

        # Emit the final production
        if production_content:
            rawsource = '\n'.join(production_lines)
            yield rawsource, production_content