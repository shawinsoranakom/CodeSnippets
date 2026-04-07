def current(self):
        if self.open_tags:
            return self.open_tags[-1]
        else:
            return self.root