def indent(self, level):
        if self.options.get("indent") is not None:
            self.xml.ignorableWhitespace(
                "\n" + " " * self.options.get("indent") * level
            )