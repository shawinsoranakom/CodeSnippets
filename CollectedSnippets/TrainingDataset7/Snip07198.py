def __iter__(self):
        "Iterate over each Geometry in the Collection."
        for i in range(len(self)):
            yield self[i]