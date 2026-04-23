def test_distributed_checkpoint_functionality(self):
        """Test OrbaxCheckpoint with distributed training.

        Verifies that a full-model checkpoint (weights + optimizer state +
        config) round-trips correctly under ModelParallel sharding.
        All predict/load calls stay inside the distribution scope so that
        JAX JIT sees the correct context mesh for sharded variables.
        """
        num_devices, device_mesh, original_distribution = (
            self._setup_distributed_test()
        )

        layout_map = self._make_layout_map(
            device_mesh, "dense_layer", "output_layer"
        )

        dense_units = self._DIST_DENSE_UNITS
        out_units = self._DIST_OUT_UNITS
        predict_batch = self._DIST_PREDICT_BATCH

        try:
            set_distribution(ModelParallel(layout_map=layout_map))
            model = self._build_distributed_model(dense_units, out_units)

            x = np.random.randn(self._DIST_NUM_SAMPLES, 10)
            y = np.random.randn(self._DIST_NUM_SAMPLES, out_units)

            checkpoint_dir = os.path.join(
                self.get_temp_dir(), "test_distributed_checkpoint"
            )
            callback = OrbaxCheckpoint(
                directory=checkpoint_dir, save_freq="epoch"
            )
            model.fit(x, y, epochs=2, callbacks=[callback], verbose=0)

            original_predictions = model.predict(x[:predict_batch], verbose=0)
            original_weights = model.get_weights()
            original_opt_vars = [v.numpy() for v in model.optimizer.variables]

            loaded = saving.load_model(checkpoint_dir)

            for orig, lw in zip(original_weights, loaded.get_weights()):
                self.assertAllClose(orig, lw)
            for orig, lv in zip(original_opt_vars, loaded.optimizer.variables):
                self.assertAllClose(orig, lv)

            loaded_predictions = loaded.predict(x[:predict_batch], verbose=0)
            self.assertAllClose(original_predictions, loaded_predictions)

            self.assertEqual(model.name, loaded.name)
            self.assertEqual(len(model.layers), len(loaded.layers))
            self.assertTrue(loaded.compiled)
            self.assertEqual(type(get_distribution()), ModelParallel)

            original_shardings = {
                var.path: var.value.sharding
                for var in model.variables
                if hasattr(var.value, "sharding")
            }
            loaded_shardings = {
                var.path: var.value.sharding
                for var in loaded.variables
                if hasattr(var.value, "sharding")
            }
            for path, spec in original_shardings.items():
                if path in loaded_shardings:
                    self.assertEqual(
                        spec,
                        loaded_shardings[path],
                        f"Sharding mismatch for variable {path}",
                    )

        finally:
            if original_distribution is not None:
                set_distribution(original_distribution)
            else:
                try:
                    set_distribution(None)
                except Exception:
                    pass