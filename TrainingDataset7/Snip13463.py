def add_blocks(self, blocks):
        for name, block in blocks.items():
            self.blocks[name].insert(0, block)