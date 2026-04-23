def _inverse_lookup(self, number):
        assert 0, "not working in the current form, but keep it as the pure python version of compact lookup"
        result = []
        node = self.root
        while 1:
            if node.final:
                if pos == 0:
                    return "".join(result)
                pos -= 1
            for label, child in sorted(node.edges.items()):
                nextpos = pos - child.num_reachable_linear
                if nextpos < 0:
                    result.append(label)
                    node = child
                    break
                else:
                    pos = nextpos
            else:
                assert 0