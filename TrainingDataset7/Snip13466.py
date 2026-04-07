def get_block(self, name):
        try:
            return self.blocks[name][-1]
        except IndexError:
            return None