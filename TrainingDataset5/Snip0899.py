def decrease_key(self, tup, new_d):
    idx = self.pos[tup[1]]
    self.array[idx] = (new_d, tup[1])
    while idx > 0 and self.array[self.par(idx)][0] > self.array[idx][0]:
        self.swap(idx, self.par(idx))
        idx = self.par(idx)
