def bind(self, sequence=None, func=None, add=None):
            #print("bind(%s, %s, %s)" % (sequence, func, add),
            #      file=sys.__stderr__)
            if type(sequence) is str and len(sequence) > 2 and \
               sequence[:2] == "<<" and sequence[-2:] == ">>":
                if sequence in self.__eventinfo:
                    ei = self.__eventinfo[sequence]
                    if ei[0] is not None:
                        for triplet in ei[1]:
                            self.__binders[triplet[1]].unbind(triplet, ei[0])
                    ei[0] = func
                    if ei[0] is not None:
                        for triplet in ei[1]:
                            self.__binders[triplet[1]].bind(triplet, func)
                else:
                    self.__eventinfo[sequence] = [func, []]
            return widget.bind(self, sequence, func, add)