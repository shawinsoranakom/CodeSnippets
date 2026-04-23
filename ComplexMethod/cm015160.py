def test_shuffler_iterdatapipe(self):
        r"""
        Verify ``IterDataPipe.shuffle`` is controlled by ``DataLoader``
        to generate different seeds deterministically per epoch.
        """
        exp = list(range(100))

        def _create_dp(buffer_size):
            input_ds = dp.iter.IterableWrapper(exp)
            return input_ds.shuffle(buffer_size=buffer_size).sharding_filter()

        for bs in (5, 20, 33):
            # Test Deterministic
            for num_workers, pw in itertools.product((0, 1, 2), (True, False)):
                if num_workers == 0 and pw:
                    continue

                shuffle_dp = _create_dp(bs)

                mp_ctx = "spawn" if num_workers > 0 else None
                dl = DataLoader(
                    shuffle_dp,
                    num_workers=num_workers,
                    shuffle=True,
                    multiprocessing_context=mp_ctx,
                    persistent_workers=pw,
                )

                # No seed
                dl_res_ns = list(dl)
                self.assertEqual(sorted(dl_res_ns), exp)

                # Same seeds
                dl_res = []
                for _epoch in range(2):
                    torch.manual_seed(123)
                    dl_res.append(list(dl))
                self.assertEqual(dl_res[0], dl_res[1])
                self.assertEqual(sorted(dl_res[0]), exp)

                # Different seeds
                torch.manual_seed(321)
                dl_res.append(list(dl))

                self.assertEqual(len(dl_res[0]), len(dl_res[2]))
                self.assertNotEqual(dl_res[0], dl_res[2])
                self.assertEqual(sorted(dl_res[0]), sorted(dl_res[2]))

                if dl._iterator is not None:
                    dl._iterator._shutdown_workers()
                    dl._iterator = None
                del dl