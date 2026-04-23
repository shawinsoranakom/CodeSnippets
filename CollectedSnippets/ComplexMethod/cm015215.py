def test_random_unary_out_of_place(
        self, device, use_generator, randomness, batched_input
    ):
        generator = torch.Generator(device=device)
        orig_state = generator.get_state()
        kwargs = {"generator": generator} if use_generator else {}
        ops = [
            lambda t, _: torch.normal(0.0, torch.abs(t), **kwargs),
            lambda t, _: torch.normal(t, 1.0, **kwargs),
            lambda t, _: torch.bernoulli(t - 0.5, **kwargs),
            lambda t, _: torch.bernoulli(t, 0.5, **kwargs),
            lambda t, _: torch._standard_gamma(t, **kwargs),
            lambda t, _: torch._sample_dirichlet(t, **kwargs),
            lambda t, _: torch.poisson(t, **kwargs),
        ]

        B0 = 4
        seed = 1234567
        in_dims = self._in_dims(batched_input)

        for op in ops:
            always_batched = torch.randn(B0, device=device)
            passed = self._get_image(batched_input, B0, device)
            if randomness == "error":
                self._assert_throws_in_error_mode(
                    op, (passed, always_batched), in_dims=in_dims
                )
                return
            if randomness == "same" and batched_input != "none":
                self._assert_throws_in_same_mode_batched(
                    op, (passed, always_batched), in_dims=in_dims
                )
                return

            generator = self._reset_random(generator, orig_state, use_generator, seed)
            vmap_result = vmap(op, in_dims=in_dims, randomness=randomness)(
                passed, always_batched
            )

            generator = self._reset_random(generator, orig_state, use_generator, seed)
            if randomness == "different":
                if batched_input == "none":
                    passed = passed.expand(B0, *passed.shape)
                if batched_input == "last":
                    passed = passed.movedim(-1, 0)
                expected = op(passed, always_batched)
                self._assert_all_slices_unique(vmap_result)
                self.assertEqual(vmap_result, expected)
            else:
                expected = op(passed, always_batched)
                self._assert_all_slices_equal(vmap_result)
                for i in range(B0):
                    self.assertEqual(vmap_result[i], expected)