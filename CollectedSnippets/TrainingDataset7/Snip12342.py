def is_summary(self):
        return any(child.is_summary for child in self.children)