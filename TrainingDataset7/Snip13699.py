def __str__(self):
        return "".join(
            [html.escape(c) if isinstance(c, str) else str(c) for c in self.children]
        )