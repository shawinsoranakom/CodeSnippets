def _check_lazy_norm(self, cls, lazy_cls, input_shape):
        for affine in [False, True]:
            for track_running_stats in [False, True]:
                lazy_module = lazy_cls(
                    affine=affine, track_running_stats=track_running_stats
                )

                if affine:
                    self.assertIsInstance(lazy_module.weight, UninitializedParameter)
                    self.assertIsInstance(lazy_module.bias, UninitializedParameter)
                if track_running_stats:
                    self.assertIsInstance(lazy_module.running_mean, UninitializedBuffer)
                    self.assertIsInstance(lazy_module.running_var, UninitializedBuffer)

                input = torch.ones(*input_shape)
                lazy_output = lazy_module(input)
                self.assertIsInstance(lazy_module, cls)
                self.assertNotIsInstance(lazy_module, lazy_cls)

                num_features = input_shape[1]
                module = cls(
                    num_features, affine=affine, track_running_stats=track_running_stats
                )
                expected_output = module(input)

                self.assertEqual(lazy_output, expected_output)
                if module.weight is not None:
                    self.assertEqual(lazy_module.weight.shape, module.weight.shape)
                    self.assertEqual(lazy_module.weight, module.weight)
                if module.bias is not None:
                    self.assertEqual(lazy_module.bias.shape, module.bias.shape)
                    self.assertEqual(lazy_module.bias, module.bias)
                if module.running_mean is not None:
                    self.assertEqual(
                        lazy_module.running_mean.shape, module.running_mean.shape
                    )
                    self.assertEqual(lazy_module.running_mean, module.running_mean)
                if module.running_var is not None:
                    self.assertEqual(
                        lazy_module.running_var.shape, module.running_var.shape
                    )
                    self.assertEqual(lazy_module.running_var, module.running_var)
                if module.num_batches_tracked is not None:
                    self.assertEqual(
                        lazy_module.num_batches_tracked.shape,
                        module.num_batches_tracked.shape,
                    )
                    self.assertEqual(
                        lazy_module.num_batches_tracked, module.num_batches_tracked
                    )