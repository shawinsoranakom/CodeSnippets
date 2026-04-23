def test_jit_fit_with_out_shardings_logic(self, distributed):
        x = np.random.rand(64, 8).astype("float32")
        y = np.random.rand(64, 1).astype("float32")

        distribution = None
        if distributed:
            if len(jax.local_devices()) < 2:
                self.skipTest(
                    "Distributed test requires at least 2 JAX devices."
                )

            devices = jax.local_devices()
            mesh = DeviceMesh(
                shape=(len(devices),), axis_names=("batch",), devices=devices
            )
            distribution = DataParallel(mesh)

        scope = distribution.scope() if distribution else mock.MagicMock()

        with scope:
            model = models.Sequential(
                [
                    layers.Dense(4, activation="relu", input_shape=(8,)),
                    layers.Dense(1),
                ]
            )
            model.compile(optimizer="adam", loss="mse", jit_compile=True)

            if distribution:
                expected_shardings = [
                    v.value.sharding for v in model.trainable_variables
                ]
                self.assertNotEqual(len(set(expected_shardings)), 1)

            model.fit(x, y, epochs=2, batch_size=32, verbose=0)

            if distribution:
                actual_shardings = [
                    v.value.sharding for v in model.trainable_variables
                ]
                self.assertListEqual(actual_shardings, expected_shardings)