def test_check_rng_sync(
        self,
        device,
    ) -> None:
        if device == "cuda" and not torch.cuda.is_available():
            self.skipTest("Cuda is not available")
        store = c10d.FileStore(self.file_name, self.world_size)
        c10d.init_process_group(
            backend="gloo", store=store, rank=self.rank, world_size=self.world_size
        )
        group = torch.distributed.distributed_c10d._get_default_group()
        generator = torch.Generator(device=device)
        generator.manual_seed(123)
        value_ranks, _ = _check_rng_sync_internal(generator, group)
        self.assertEqual(len(value_ranks), 1, value_ranks)
        for actual, expected in zip(value_ranks.values(), [{0, 1, 2, 3}]):
            self.assertEqual(actual, expected, actual)

        if torch.distributed.get_rank() == 1:
            torch.randn((10,), device=device, generator=generator)
        value_ranks, _ = _check_rng_sync_internal(generator, group)
        self.assertEqual(len(value_ranks), 2, value_ranks)
        for actual, expected in zip(value_ranks.values(), [{0, 2, 3}, {1}]):
            self.assertEqual(actual, expected, actual)

        if torch.distributed.get_rank() == 0:
            generator.manual_seed(456)
        value_ranks, _ = _check_rng_sync_internal(generator, group)
        self.assertEqual(len(value_ranks), 3, value_ranks)
        for actual, expected in zip(value_ranks.values(), [{0}, {1}, {2, 3}]):
            self.assertEqual(actual, expected, actual)

        log_str = _check_rng_sync(generator, group)
        FileCheck().check("Generator desync detected").check("Ranks").check("0").check(
            "1"
        ).check("2:4").run(log_str)