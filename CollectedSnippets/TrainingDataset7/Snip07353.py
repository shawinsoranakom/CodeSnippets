def __iter__(self):
        "Allow iteration over this LineString."
        for i in range(len(self)):
            yield self[i]