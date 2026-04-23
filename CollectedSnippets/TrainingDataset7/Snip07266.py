def __hash__(self):
        return hash((self.srid, self.wkt))