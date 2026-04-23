def __getitem__(self, idx):
                return super().__getitem__(len(self) - idx - 1)