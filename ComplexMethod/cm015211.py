def test_like_functions(self, device, randomness, batched_input):
        seed = 1234567
        supported_ops = [
            lambda t, _: torch.randint_like(t, 20),
            lambda t, _: torch.randint_like(t, 0, 20),
            lambda t, _: torch.rand_like(t),
            lambda t, _: torch.randn_like(t),
        ]
        B0 = 4

        for op in supported_ops:
            always_batched = torch.randn(B0)
            passed = self._get_image(batched_input, B0, device)
            in_dims = self._in_dims(batched_input)

            if randomness == "error":
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"called random operation while in randomness error mode",
                ):
                    vmap(op, in_dims=in_dims, randomness=randomness)(
                        passed, always_batched
                    )
                return

            torch.manual_seed(seed)
            vmap_result = vmap(op, randomness=randomness, in_dims=in_dims)(
                passed, always_batched
            )

            torch.manual_seed(seed)

            if batched_input == "last":
                passed = passed.movedim(-1, 0)
            if randomness == "different":
                if batched_input == "none":
                    passed = passed.expand(B0, *passed.shape)
                expected = op(passed, 0)

                self._assert_all_slices_unique(vmap_result)
                # RNG differs between eager and via dynamo trace on CUDA
                if not (TEST_WITH_TORCHDYNAMO and torch.device(device).type == "cuda"):
                    self.assertEqual(expected, vmap_result)
                return

            if randomness != "same":
                raise AssertionError(
                    f"Expected randomness to be 'same', got '{randomness}'"
                )
            if batched_input != "none":
                passed = passed[0]
            expected = op(passed, 0)
            self._assert_all_slices_equal(vmap_result)
            # RNG differs between eager and via dynamo trace on CUDA
            if not (TEST_WITH_TORCHDYNAMO and torch.device(device).type == "cuda"):
                for i in range(B0):
                    self.assertEqual(expected, vmap_result[i])