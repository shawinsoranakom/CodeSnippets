def __getitem__(self, idx):
        if isinstance(idx, int):
            idx = slice(idx, idx)

        # NB: PlaylistEntries[1:10] => (0, 1, ... 9)
        step = 1 if idx.step is None else idx.step
        if idx.start is None:
            start = 0 if step > 0 else len(self) - 1
        else:
            start = idx.start - 1 if idx.start >= 0 else len(self) + idx.start

        # NB: Do not call len(self) when idx == [:]
        if idx.stop is None:
            stop = 0 if step < 0 else float('inf')
        else:
            stop = idx.stop - 1 if idx.stop >= 0 else len(self) + idx.stop
        stop += [-1, 1][step > 0]

        for i in frange(start, stop, step):
            if i < 0:
                continue
            try:
                entry = self._getter(i)
            except self.IndexError:
                self.is_exhausted = True
                if step > 0:
                    break
                continue
            yield i + 1, entry