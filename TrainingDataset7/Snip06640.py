def __eq__(self, other):
        return isinstance(other, PostGISAdapter) and self.ewkb == other.ewkb