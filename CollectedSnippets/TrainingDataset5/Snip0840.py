def bezier_curve_function(self, t: float) -> tuple[float, float]:

    assert 0 <= t <= 1, "Time t must be between 0 and 1."

    basis_function = self.basis_function(t)
    x = 0.0
    y = 0.0
    for i in range(len(self.list_of_points)):
        x += basis_function[i] * self.list_of_points[i][0]
        y += basis_function[i] * self.list_of_points[i][1]
    return (x, y)
