def text(self):
        return self.content.decode(self.charset or "utf-8")