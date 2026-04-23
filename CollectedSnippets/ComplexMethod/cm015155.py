def test_iterable_style_dataset(self):
        # [no auto-batching] single process loading
        dataset = CountingIterableDataset(20)
        dataloader = self._get_data_loader(dataset, batch_size=None)
        fetched = list(dataloader)
        self.assertEqual(len(fetched), 20)
        for i, d in enumerate(fetched):
            # non-batched should not convert ints into tensors
            self.assertIsInstance(d, int)
            self.assertEqual(d, i)
        # DataLoader should match len of the iterable-style dataset (if implemented)
        self.assertEqual(len(dataloader), len(dataset))

        # [no auto-batching] multiprocessing loading
        num_workers = 3
        sizes_for_all_workers = [0, 4, 20]
        expected = sorted(
            functools.reduce(
                operator.iadd, (list(range(s)) for s in sizes_for_all_workers), []
            )
        )
        if len(sizes_for_all_workers) != num_workers:
            raise AssertionError("invalid test case")
        for prefetch_factor in [2, 3, 4]:
            dataset = WorkerSpecificIterableDataset(sizes_for_all_workers)
            dataloader = self._get_data_loader(
                dataset,
                num_workers=num_workers,
                batch_size=None,
                worker_init_fn=set_faulthander_if_available,
                prefetch_factor=prefetch_factor,
            )
            dataloader_iter = iter(dataloader)
            fetched = sorted(dataloader_iter)
            for a, b in zip(fetched, expected):
                # non-batched should not convert ints into tensors
                self.assertIsInstance(a, int)
                self.assertEqual(a, b)
            # DataLoader should match len of the iterable-style dataset (if implemented)
            self.assertEqual(len(dataloader), len(dataset))
            # When loading more than len(dataset) data, after accessing len(dataloader),
            # we should get a warning. See NOTE [ IterableDataset and __len__ ].
            dataset = CountingIterableDataset(20)
            dataloader = self._get_data_loader(
                dataset,
                num_workers=num_workers,
                worker_init_fn=set_faulthander_if_available,
                prefetch_factor=prefetch_factor,
            )
            it = iter(dataloader)
            for _ in range(40):
                self.assertNotWarn(
                    lambda: next(it), "Should not warn before accessing len(dataloader)"
                )
            self.assertEqual(len(dataloader), len(dataset))
            self.assertEqual(len(dataloader), 20)
            it = iter(dataloader)
            for _ in range(20):
                self.assertNotWarn(
                    lambda: next(it), "Should not warn before exceeding length"
                )
            for _ in range(3):
                with self.assertWarnsRegex(
                    UserWarning,
                    r"but [0-9]+ samples have been fetched\. For multiprocessing data-loading, this",
                    msg="Should always warn after exceeding length",
                ):
                    next(it)
        # [no auto-batching] test that workers exit gracefully
        workers = dataloader_iter._workers
        del dataloader_iter
        del dataloader
        try:
            for w in workers:
                w.join(JOIN_TIMEOUT)
                self.assertFalse(w.is_alive())
                self.assertEqual(w.exitcode, 0)
        finally:
            for w in workers:
                w.terminate()

        # [auto-batching] single process loading
        dataset = CountingIterableDataset(20)
        fetched = list(self._get_data_loader(dataset, batch_size=7))
        self.assertEqual(len(fetched), 3)
        self.assertEqual(fetched[0].tolist(), list(range(7)))
        self.assertEqual(fetched[1].tolist(), list(range(7, 14)))
        self.assertEqual(fetched[2].tolist(), list(range(14, 20)))

        # [auto-batching] multiprocessing loading
        num_workers = 3
        sizes_for_all_workers = [0, 4, 20]
        expected = sorted(
            functools.reduce(
                operator.iadd, (list(range(s)) for s in sizes_for_all_workers), []
            )
        )
        if len(sizes_for_all_workers) != num_workers:
            raise AssertionError("invalid test case")
        for prefetch_factor in [2, 3, 4]:
            dataset = WorkerSpecificIterableDataset(sizes_for_all_workers)
            # worker 0 should return 0 batches
            # worker 1 should return 1 batches
            # worker 2 should return 3 batches
            dataloader = self._get_data_loader(
                dataset,
                num_workers=num_workers,
                batch_size=7,
                prefetch_factor=prefetch_factor,
            )
            dataloader_iter = iter(dataloader)
            fetched = list(dataloader_iter)
            self.assertEqual(len(fetched), 4)
            fetched = {tuple(t.tolist()) for t in fetched}
            self.assertEqual(
                fetched,
                {
                    tuple(range(4)),
                    tuple(range(7)),
                    tuple(range(7, 14)),
                    tuple(range(14, 20)),
                },
            )

            # [auto-batching] test that workers exit gracefully
            workers = dataloader_iter._workers
            del dataloader_iter
            del dataloader
            try:
                for w in workers:
                    w.join(JOIN_TIMEOUT)
                    self.assertFalse(w.is_alive())
                    self.assertEqual(w.exitcode, 0)
            finally:
                for w in workers:
                    w.terminate()
        # [auto-batching & drop_last] single process loading
        dataset = CountingIterableDataset(20)
        fetched = list(self._get_data_loader(dataset, batch_size=7, drop_last=True))
        self.assertEqual(len(fetched), 2)
        self.assertEqual(fetched[0].tolist(), list(range(7)))
        self.assertEqual(fetched[1].tolist(), list(range(7, 14)))

        # [auto-batching & drop_last] multiprocessing loading
        num_workers = 3
        sizes_for_all_workers = [0, 4, 20]
        expected = sorted(
            functools.reduce(
                operator.iadd, (list(range(s)) for s in sizes_for_all_workers), []
            )
        )
        if len(sizes_for_all_workers) != num_workers:
            raise AssertionError("invalid test case")
        for prefetch_factor in [2, 3, 4]:
            dataset = WorkerSpecificIterableDataset(sizes_for_all_workers)
            # worker 0 should return 0 batches
            # worker 1 should return 1 batches
            # worker 2 should return 3 batches
            dataloader = self._get_data_loader(
                dataset,
                num_workers=num_workers,
                batch_size=7,
                drop_last=True,
                worker_init_fn=set_faulthander_if_available,
                prefetch_factor=prefetch_factor,
            )
            dataloader_iter = iter(dataloader)
            fetched = list(dataloader_iter)
            self.assertEqual(len(fetched), 2)
            fetched = {tuple(t.tolist()) for t in fetched}
            self.assertEqual(fetched, {tuple(range(7)), tuple(range(7, 14))})

            # [auto-batching & drop_last] test that workers exit gracefully
            workers = dataloader_iter._workers
            del dataloader_iter
            del dataloader
            try:
                for w in workers:
                    w.join(JOIN_TIMEOUT)
                    self.assertFalse(w.is_alive())
                    self.assertEqual(w.exitcode, 0)
            finally:
                for w in workers:
                    w.terminate()