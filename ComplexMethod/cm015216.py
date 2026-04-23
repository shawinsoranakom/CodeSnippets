def test_multinomial(
        self, device, use_generator, randomness, batched_call, batched_input
    ):
        def flatten_input(input, batch_call, batch_location):
            if batch_call and batch_location != "none":
                final_size = 3  # [B0, B, N]
            elif not batch_call and batch_location == "none":
                final_size = 1  # [N]
            else:
                final_size = 2  # [B0, N] or [B, N]

            start_idx = final_size - 1
            end_idx = -1
            if batch_location == "last":
                start_idx -= 1
                end_idx -= (
                    1  # gets to correct final size because using negative indices
                )

            ret = input.flatten(start_idx, end_idx)
            if ret.dim() != final_size:
                raise AssertionError(f"Expected dim {final_size}, got {ret.dim()}")
            return ret

        def op(input, _):
            return torch.multinomial(input, 10, **kwargs)

        generator = torch.Generator(device=device)
        orig_state = generator.get_state()
        kwargs = {"generator": generator} if use_generator else {}

        B0 = 4
        seed = 1234567
        in_dims = self._in_dims(batched_input)

        always_batched = torch.randn(B0, device=device)
        passed = self._get_image(batched_input, B0, device)
        passed = flatten_input(passed, batched_call, batched_input)
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
            orig_passed_size = passed.shape[:2] if batched_call else passed.shape[:1]
            passed = passed.flatten(0, 1) if batched_call else passed
            expected = op(passed, always_batched)
            expected = expected.reshape(*orig_passed_size, 10)
            self._assert_all_slices_unique(vmap_result)
            self.assertEqual(vmap_result, expected)
        else:
            expected = op(passed, always_batched)
            self._assert_all_slices_equal(vmap_result)
            for i in range(B0):
                self.assertEqual(vmap_result[i], expected)