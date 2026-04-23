def test_partial_workers(self):
        r"""Check that workers exit even if the iterator is not exhausted."""
        if TEST_CUDA:
            pin_memory_configs = (True, False)
        else:
            pin_memory_configs = (False,)

        for pin_memory in pin_memory_configs:
            loader = iter(
                self._get_data_loader(
                    self.dataset, batch_size=2, num_workers=4, pin_memory=pin_memory
                )
            )
            workers = loader._workers
            if pin_memory:
                pin_memory_thread = loader._pin_memory_thread
            for i, _ in enumerate(loader):
                if i == 10:
                    break
            if i != 10:
                raise AssertionError(f"Expected to stop at i=10, got i={i}")
            del loader
            for w in workers:
                w.join(JOIN_TIMEOUT)
                self.assertFalse(w.is_alive(), "subprocess not terminated")
            if pin_memory:
                pin_memory_thread.join(JOIN_TIMEOUT)
                self.assertFalse(pin_memory_thread.is_alive())