def test_bernoulli_in_place(
        self, device, use_generator, randomness, batched_input, batched_probability
    ):
        B0 = 4
        seed = 1234567
        generator = torch.Generator(device=device)
        orig_state = generator.get_state()
        kwargs = {"generator": generator} if use_generator else {}
        in_dims = self._in_dims(batched_input, batched_probability)

        def op(t, p, ignored):
            return t.bernoulli_(p, **kwargs)

        # because of in place updates, clone inputs
        always_batched = torch.randn(B0, device=device)
        input = self._get_image(batched_input, B0, device)
        input_expected = input.clone()
        probability = self._get_image(batched_probability, B0, device) - 0.5

        if randomness == "error":
            self._assert_throws_in_error_mode(
                op, (input, probability, always_batched), in_dims=in_dims
            )
            return
        if randomness == "same" and batched_probability != "none":
            self._assert_throws_in_same_mode_batched(
                op, (input, probability, always_batched), in_dims=in_dims
            )
            return
        if batched_input == "none" and batched_probability != "none":
            regex = r"there exists a Tensor `other` in extra_args that has more elements than `self`"
            with self.assertRaisesRegex(RuntimeError, regex):
                vmap(op, in_dims=in_dims, randomness=randomness)(
                    input, probability, always_batched
                )
            return
        if randomness == "different" and batched_input == "none":
            self._assert_throws_in_different_mode_inplace(
                op, (input, probability, always_batched), in_dims=in_dims
            )
            return

        self._reset_random(generator, orig_state, use_generator, seed)
        vmap_result = vmap(op, in_dims=in_dims, randomness=randomness)(
            input, probability, always_batched
        )

        self._reset_random(generator, orig_state, use_generator, seed)
        if batched_input == "last":
            input_expected = input_expected.movedim(-1, 0)
        if batched_probability == "last":
            probability = probability.movedim(-1, 0)
        if randomness == "different":
            expected = op(input_expected, probability, always_batched)
            self._assert_all_slices_unique(vmap_result)
            self.assertEqual(vmap_result, expected)
        else:
            if batched_input != "none":
                input_expected = input_expected[0]
            expected = op(input_expected, probability, always_batched)
            self._assert_all_slices_equal(vmap_result)
            for i in range(B0):
                self.assertEqual(vmap_result[i], expected)