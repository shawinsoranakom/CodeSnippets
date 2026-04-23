def __str__(self):
        type_str = "an int" if self.type is Integral else "a float"
        left_bracket = "[" if self.closed in ("left", "both") else "("
        left_bound = "-inf" if self.left is None else self.left
        right_bound = "inf" if self.right is None else self.right
        right_bracket = "]" if self.closed in ("right", "both") else ")"

        # better repr if the bounds were given as integers
        if not self.type == Integral and isinstance(self.left, Real):
            left_bound = float(left_bound)
        if not self.type == Integral and isinstance(self.right, Real):
            right_bound = float(right_bound)

        return (
            f"{type_str} in the range "
            f"{left_bracket}{left_bound}, {right_bound}{right_bracket}"
        )