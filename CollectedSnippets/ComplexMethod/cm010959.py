def __eq__(self, other):
        if not isinstance(other, AffineTransform):
            return False

        if isinstance(self.loc, _Number) and isinstance(other.loc, _Number):
            if self.loc != other.loc:
                return False
        else:
            if not (self.loc == other.loc).all().item():  # type: ignore[union-attr]
                return False

        if isinstance(self.scale, _Number) and isinstance(other.scale, _Number):
            if self.scale != other.scale:
                return False
        else:
            if not (self.scale == other.scale).all().item():  # type: ignore[union-attr]
                return False

        return True