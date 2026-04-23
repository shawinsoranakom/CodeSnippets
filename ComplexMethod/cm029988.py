def _find_cycle(self):
        n2i = self._node2info
        stack = []
        itstack = []
        seen = set()
        node2stacki = {}

        for node in n2i:
            if node in seen:
                continue

            while True:
                if node in seen:
                    if node in node2stacki:
                        return stack[node2stacki[node] :] + [node]
                    # else go on to get next successor
                else:
                    seen.add(node)
                    itstack.append(iter(n2i[node].successors).__next__)
                    node2stacki[node] = len(stack)
                    stack.append(node)

                # Backtrack to the topmost stack entry with
                # at least another successor.
                while stack:
                    try:
                        node = itstack[-1]()
                        break # resume at top of "while True:"
                    except StopIteration:
                        # no more successors; pop the stack
                        # and continue looking up
                        del node2stacki[stack.pop()]
                        itstack.pop()
                else:
                    # stack is empty; look for a fresh node to
                    # start over from (a node not yet in seen)
                    break
        return None