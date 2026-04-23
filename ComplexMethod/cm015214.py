def test_random_binary_out_of_place(
        self, device, use_generator, randomness, batched_input, batched_other
    ):
        generator = torch.Generator(device=device)
        orig_state = generator.get_state()
        kwargs = {"generator": generator} if use_generator else {}
        ops = [
            lambda t, o, _: torch.normal(t, o, **kwargs),
            lambda t, o, _: torch.binomial(t, (o - 0.5), **kwargs),
        ]

        B0 = 4
        seed = 1234567
        in_dims = self._in_dims(batched_input, batched_other)

        for op in ops:
            always_batched = torch.randn(B0, device=device)
            input = self._get_image(batched_input, B0, device)
            other = self._get_image(batched_other, B0, device)

            if randomness == "error":
                self._assert_throws_in_error_mode(
                    op, (input, other, always_batched), in_dims=in_dims
                )
                return
            if randomness == "same" and (
                batched_input != "none" or batched_other != "none"
            ):
                self._assert_throws_in_same_mode_batched(
                    op, (input, other, always_batched), in_dims=in_dims
                )
                return

            generator = self._reset_random(generator, orig_state, use_generator, seed)
            vmap_result = vmap(op, in_dims=in_dims, randomness=randomness)(
                input, other, always_batched
            )

            if batched_input == "last":
                input = input.movedim(-1, 0)
            if batched_other == "last":
                other = other.movedim(-1, 0)

            generator = self._reset_random(generator, orig_state, use_generator, seed)
            if randomness == "different":
                if batched_input == "none":
                    input = input.expand(B0, *input.shape)
                expected = op(input, other, always_batched)
                self._assert_all_slices_unique(vmap_result)
                self.assertEqual(vmap_result, expected)
            else:
                if batched_input != "none" or batched_other != "none":
                    raise AssertionError(
                        f"Expected batched_input='none' and batched_other='none', "
                        f"got batched_input='{batched_input}' and "
                        f"batched_other='{batched_other}'"
                    )
                expected = op(input, other, always_batched)
                self._assert_all_slices_equal(vmap_result)
                for i in range(B0):
                    self.assertEqual(vmap_result[i], expected)