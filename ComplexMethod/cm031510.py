def unbind(self, sequence, funcid=None):
            if type(sequence) is str and len(sequence) > 2 and \
               sequence[:2] == "<<" and sequence[-2:] == ">>" and \
               sequence in self.__eventinfo:
                func, triplets = self.__eventinfo[sequence]
                if func is not None:
                    for triplet in triplets:
                        self.__binders[triplet[1]].unbind(triplet, func)
                    self.__eventinfo[sequence][0] = None
            return widget.unbind(self, sequence, funcid)