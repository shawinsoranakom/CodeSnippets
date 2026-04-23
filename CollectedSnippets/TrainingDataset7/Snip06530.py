def __hash__(self):
        return hash((self.wkt, self.srid))