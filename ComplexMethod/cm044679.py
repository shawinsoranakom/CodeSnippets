def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = options.max_width

        characters = (
            "-"
            if (options.ascii_only and not self.characters.isascii())
            else self.characters
        )

        chars_len = cell_len(characters)
        if not self.title:
            yield self._rule_line(chars_len, width)
            return

        if isinstance(self.title, Text):
            title_text = self.title
        else:
            title_text = console.render_str(self.title, style="rule.text")

        title_text.plain = title_text.plain.replace("\n", " ")
        title_text.expand_tabs()

        required_space = 4 if self.align == "center" else 2
        truncate_width = max(0, width - required_space)
        if not truncate_width:
            yield self._rule_line(chars_len, width)
            return

        rule_text = Text(end=self.end)
        if self.align == "center":
            title_text.truncate(truncate_width, overflow="ellipsis")
            side_width = (width - cell_len(title_text.plain)) // 2
            left = Text(characters * (side_width // chars_len + 1))
            left.truncate(side_width - 1)
            right_length = width - cell_len(left.plain) - cell_len(title_text.plain)
            right = Text(characters * (side_width // chars_len + 1))
            right.truncate(right_length)
            rule_text.append(left.plain + " ", self.style)
            rule_text.append(title_text)
            rule_text.append(" " + right.plain, self.style)
        elif self.align == "left":
            title_text.truncate(truncate_width, overflow="ellipsis")
            rule_text.append(title_text)
            rule_text.append(" ")
            rule_text.append(characters * (width - rule_text.cell_len), self.style)
        elif self.align == "right":
            title_text.truncate(truncate_width, overflow="ellipsis")
            rule_text.append(characters * (width - title_text.cell_len - 1), self.style)
            rule_text.append(" ")
            rule_text.append(title_text)

        rule_text.plain = set_cell_size(rule_text.plain, width)
        yield rule_text