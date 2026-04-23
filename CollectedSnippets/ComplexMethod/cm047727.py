def __le__(self, other: Leaf) -> bool:
        if self.is_empty() or other.is_universal():
            return True
        elif self.is_universal() or other.is_empty():
            return False
        elif self.negative:
            return other.negative and ~other <= ~self
        elif other.negative:
            return self.id in other.disjoints
        else:
            return self.id in other.subsets