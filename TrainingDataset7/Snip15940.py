def _connect(self, i, j):
        self.objs[i].parent = self.objs[j]
        self.objs[i].save()