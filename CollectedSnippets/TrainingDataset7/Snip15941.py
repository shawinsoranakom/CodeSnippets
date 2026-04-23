def _collect(self, *indices):
        self.n.collect([self.objs[i] for i in indices])