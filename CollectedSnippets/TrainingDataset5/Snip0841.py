def plot_curve(self, step_size: float = 0.01):
    from matplotlib import pyplot as plt

    to_plot_x: list[float] = []
    to_plot_y: list[float] = []

    t = 0.0
    while t <= 1:
        value = self.bezier_curve_function(t)
        to_plot_x.append(value[0])
        to_plot_y.append(value[1])
        t += step_size

    x = [i[0] for i in self.list_of_points]
    y = [i[1] for i in self.list_of_points]

    plt.plot(
        to_plot_x,
        to_plot_y,
        color="blue",
        label="Curve of Degree " + str(self.degree),
    )
    plt.scatter(x, y, color="red", label="Control Points")
    plt.legend()
    plt.show()
