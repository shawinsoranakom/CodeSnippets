def test_randperm(self, device, randomness, use_generator):
        # needs a special case because randperm doesn't take a batch size
        B0 = 4
        seed = 1234567
        passed = torch.randn(B0, device=device)

        torch.manual_seed(seed)
        generator = torch.Generator(device=device)
        orig_state = generator.get_state()

        kwargs = (
            {"device": device, "generator": generator}
            if use_generator
            else {"device": device}
        )

        if randomness == "error":
            with self.assertRaisesRegex(
                RuntimeError, r"called random operation while in randomness error mode"
            ):
                vmap(lambda _: torch.randperm(10, **kwargs), randomness=randomness)(
                    passed
                )
            return

        vmap_result = vmap(
            lambda _: torch.randperm(10, **kwargs), randomness=randomness
        )(passed)
        generator = generator.set_state(orig_state)
        torch.manual_seed(seed)
        if randomness == "different":
            for i in range(B0):
                expected = torch.randperm(10, **kwargs)
                # RNG differs between eager and via dynamo trace on CUDA
                if TEST_WITH_TORCHDYNAMO and torch.device(device).type == "cuda":
                    self._assert_all_slices_unique(vmap_result)
                else:
                    self.assertEqual(vmap_result[i], expected)
        else:
            expected = torch.randperm(10, **kwargs)
            # RNG differs between eager and via dynamo trace on CUDA
            if TEST_WITH_TORCHDYNAMO and torch.device(device).type == "cuda":
                self._assert_all_slices_equal(vmap_result)
            else:
                for i in range(B0):
                    self.assertEqual(vmap_result[i], expected)