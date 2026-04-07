def __eq__(self, other):
        "Is this Geometry equal to the other?"
        return isinstance(other, OGRGeometry) and self.equals(other)