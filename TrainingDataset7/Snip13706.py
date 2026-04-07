def handle_endtag(self, tag):
        if not self.open_tags:
            self.error("Unexpected end tag `%s` (%s)" % (tag, self.format_position()))
        element = self.open_tags.pop()
        while element.name != tag:
            if not self.open_tags:
                self.error(
                    "Unexpected end tag `%s` (%s)" % (tag, self.format_position())
                )
            element = self.open_tags.pop()