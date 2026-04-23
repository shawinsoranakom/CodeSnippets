def __iter__(self):
        for idx in range(1, len(self) + 1):
            yield GDALBand(self.source, idx)