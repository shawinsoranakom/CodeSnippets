def membership(self, x: float) -> float:
    if x <= self.left_boundary or x >= self.right_boundary:
        return 0.0
    elif self.left_boundary < x <= self.peak:
        return (x - self.left_boundary) / (self.peak - self.left_boundary)
    elif self.peak < x < self.right_boundary:
        return (self.right_boundary - x) / (self.right_boundary - self.peak)
    msg = f"Invalid value {x} for fuzzy set {self}"
    raise ValueError(msg)
