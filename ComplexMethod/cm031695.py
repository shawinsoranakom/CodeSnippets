def _find_live_blocks(self) -> set[_Block]:
        live: set[_Block] = set()
        # Externally reachable blocks are live
        todo: set[_Block] = {b for b in self._blocks() if b.label in self.globals}
        while todo:
            block = todo.pop()
            live.add(block)
            if block.fallthrough:
                next = block.link
                if next is not None and next not in live:
                    todo.add(next)
            next = block.target
            if next is not None and next not in live:
                todo.add(next)
        return live