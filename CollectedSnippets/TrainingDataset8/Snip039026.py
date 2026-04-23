def setUp(self):
        super().setUp()
        if matplotlib.get_backend().lower() != "agg":
            plt.switch_backend("agg")