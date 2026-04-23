def advance_hard(vmid=(m-1)/2.0, hmid=(n-1)/2.0, len=len):
            # If some successor has only one exit, must take it.
            # Else favor successors with fewer exits.
            # Break ties via max distance from board centerpoint (favor
            # corners and edges whenever possible).
            candidates = []
            for i in succs[self.lastij]:
                e = len(succs[i])
                assert e > 0, "else remove_from_successors() pruning flawed"
                if e == 1:
                    candidates = [(e, 0, i)]
                    break
                i1, j1 = self.index2coords(i)
                d = (i1 - vmid)**2 + (j1 - hmid)**2
                candidates.append((e, -d, i))
            else:
                candidates.sort()

            for e, d, i in candidates:
                if i != self.final:
                    if remove_from_successors(i):
                        self.lastij = i
                        yield i
                    add_to_successors(i)