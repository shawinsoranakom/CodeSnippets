def root_attributes(self):
        if self.feed["language"] is not None:
            return {"xmlns": self.ns, "xml:lang": self.feed["language"]}
        else:
            return {"xmlns": self.ns}