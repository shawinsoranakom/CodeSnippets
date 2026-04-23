def test_random_unary_inplace(
        self, device, use_generator, randomness, batched_input
    ):
        generator = torch.Generator(device=device)
        orig_state = generator.get_state()
        kwargs = {"generator": generator} if use_generator else {}
        ops = [
            lambda t, _: t.random_(**kwargs),
            lambda t, _: t.random_(100, **kwargs),
            lambda t, _: t.random_(-5, 100, **kwargs),
            lambda t, _: t.normal_(**kwargs),
            lambda t, _: t.bernoulli_(**kwargs),
            lambda t, _: t.cauchy_(**kwargs),
            lambda t, _: t.exponential_(**kwargs),
            lambda t, _: t.geometric_(0.5, **kwargs),
            lambda t, _: t.log_normal_(**kwargs),
            lambda t, _: t.uniform_(**kwargs),
        ]
        B0 = 4
        seed = 1234567
        in_dims = self._in_dims(batched_input)

        for op in ops:
            # because of in place updates, clone inputs
            always_batched = torch.randn(B0, device=device)
            passed = self._get_image(batched_input, B0, device)
            passed_expected = passed.clone()

            if randomness == "error":
                self._assert_throws_in_error_mode(
                    op, (passed, always_batched), in_dims=in_dims
                )
                return
            if randomness == "different" and batched_input == "none":
                self._assert_throws_in_different_mode_inplace(
                    op, (passed, always_batched), in_dims=in_dims
                )
                return

            generator = self._reset_random(generator, orig_state, use_generator, seed)
            vmap_result = vmap(op, in_dims=in_dims, randomness=randomness)(
                passed, always_batched
            )

            if batched_input == "last":
                passed_expected = passed_expected.movedim(-1, 0)
            generator = self._reset_random(generator, orig_state, use_generator, seed)
            if randomness == "different":
                expected = op(passed_expected, always_batched)
                self._assert_all_slices_unique(vmap_result)
                self.assertEqual(vmap_result, expected)
            else:
                if batched_input != "none":
                    passed_expected = passed_expected[
                        0
                    ].clone()  # bug in pytorch, normal_ on views doesn't work
                expected = op(passed_expected, always_batched)
                self._assert_all_slices_equal(vmap_result)
                for i in range(B0):
                    self.assertEqual(vmap_result[i], expected)