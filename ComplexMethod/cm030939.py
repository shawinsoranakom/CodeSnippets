def advance(len=len):
            # If some successor has only one exit, must take it.
            # Else favor successors with fewer exits.
            candidates = []
            for i in succs[self.lastij]:
                e = len(succs[i])
                assert e > 0, "else remove_from_successors() pruning flawed"
                if e == 1:
                    candidates = [(e, i)]
                    break
                candidates.append((e, i))
            else:
                candidates.sort()

            for e, i in candidates:
                if i != self.final:
                    if remove_from_successors(i):
                        self.lastij = i
                        yield i
                    add_to_successors(i)