def extract_visible_text(self, html: str) -> str:
        self.reset()
        self.text_parts = []
        self.feed(html)
        return "".join(self.text_parts).strip()