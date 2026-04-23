def basis_function(self, t: float) -> list[float]:
    assert 0 <= t <= 1, "Time t must be between 0 and 1."
    output_values: list[float] = []
    for i in range(len(self.list_of_points)):
        output_values.append(
            comb(self.degree, i) * ((1 - t) ** (self.degree - i)) * (t**i)
        )
    assert round(sum(output_values), 5) == 1
    return output_values
