def tearDown(self):
        # Clear the global pyplot figure between tests
        plt.clf()
        super().tearDown()