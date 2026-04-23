def test_meshgrid(self):
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])
        z = np.array([7, 8, 9])

        for mg_knp, mg_np in zip(knp.meshgrid(x, y), np.meshgrid(x, y)):
            self.assertAllClose(mg_knp, mg_np)

        for mg_knp, mg_np in zip(knp.meshgrid(x, z), np.meshgrid(x, z)):
            self.assertAllClose(mg_knp, mg_np)

        for mg_knp, mg_np in zip(
            knp.meshgrid(x, y, z, indexing="ij"),
            np.meshgrid(x, y, z, indexing="ij"),
        ):
            self.assertAllClose(mg_knp, mg_np)

        for mg_knp, mg_np in zip(knp.Meshgrid()(x, y), np.meshgrid(x, y)):
            self.assertAllClose(mg_knp, mg_np)

        for mg_knp, mg_np in zip(knp.Meshgrid()(x, z), np.meshgrid(x, z)):
            self.assertAllClose(mg_knp, mg_np)

        for mg_knp, mg_np in zip(
            knp.Meshgrid(indexing="ij")(x, y, z),
            np.meshgrid(x, y, z, indexing="ij"),
        ):
            self.assertAllClose(mg_knp, mg_np)

        if backend.backend() == "tensorflow":
            # Arguments to `jax.numpy.meshgrid` must be 1D now.
            x = np.ones([1, 2, 3])
            y = np.ones([4, 5, 6, 6])
            z = np.ones([7, 8])
            self.assertAllClose(knp.meshgrid(x, y), np.meshgrid(x, y))
            self.assertAllClose(knp.meshgrid(x, z), np.meshgrid(x, z))
            self.assertAllClose(
                knp.meshgrid(x, y, z, indexing="ij"),
                np.meshgrid(x, y, z, indexing="ij"),
            )
            self.assertAllClose(knp.Meshgrid()(x, y), np.meshgrid(x, y))
            self.assertAllClose(knp.Meshgrid()(x, z), np.meshgrid(x, z))
            self.assertAllClose(
                knp.Meshgrid(indexing="ij")(x, y, z),
                np.meshgrid(x, y, z, indexing="ij"),
            )