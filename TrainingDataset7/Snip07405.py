def __iter__(self):
        "Iterate over coordinates of this Point."
        for i in range(len(self)):
            yield self[i]