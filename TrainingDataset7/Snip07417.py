def __iter__(self):
        "Iterate over each ring in the polygon."
        for i in range(len(self)):
            yield self[i]