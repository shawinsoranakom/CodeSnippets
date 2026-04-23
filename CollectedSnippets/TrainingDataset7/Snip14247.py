def discard(self, item):
        try:
            self.remove(item)
        except KeyError:
            pass