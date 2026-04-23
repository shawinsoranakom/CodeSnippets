def __init__(self, *, coords=None, centroid=None, ext_ring_cs=None, **kwargs):
        # Converting lists to tuples of certain keyword args
        # so coordinate test cases will match (JSON has no
        # concept of tuple).
        if coords:
            self.coords = tuplize(coords)
        if centroid:
            self.centroid = tuple(centroid)
        self.ext_ring_cs = ext_ring_cs and tuplize(ext_ring_cs)
        super().__init__(**kwargs)