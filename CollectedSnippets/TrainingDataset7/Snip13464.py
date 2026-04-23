def pop(self, name):
        try:
            return self.blocks[name].pop()
        except IndexError:
            return None