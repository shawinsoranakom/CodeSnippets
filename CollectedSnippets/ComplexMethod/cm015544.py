def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        res = func(*args, **(kwargs or {}))

        if func in collective_ops:
            if func != _c10d_functional.wait_tensor.default:
                pg = CollectiveOp.get_process_group(func, args)
                self.test.assertIsInstance(
                    pg, ProcessGroup, "Error: pg is not an instance of ProcessGroup"
                )
                self.test.assertEqual(
                    pg, dist.group.WORLD, "Error: pg is not equal to dist.group.WORLD"
                )
                self.test.assertEqual(
                    pg.size(),
                    4,
                    f"Error: Expected pg.size() to be 4, but got {pg.size()}",
                )
                self.test.assertNotEqual(
                    pg.name(), "", "Error: pg.name() should not be an empty string"
                )

            if func not in CollectiveTest.collective_size_exclude:
                # Compute expected communication tensor size
                computed_size = CollectiveOp.get_comm_tensor_size(
                    func, res, args, kwargs
                )
                expected_size = self.get_expected_size(func, res, args, kwargs)

                self.test.assertEqual(
                    computed_size,
                    expected_size,
                    msg=f"Size mismatch for {func.__name__}: expected {expected_size}, got {computed_size}",
                )

        if (
            func in non_functional_collectives
            and func != c10d.monitored_barrier_.default
        ):
            work = res[-1] if isinstance(res, (tuple, list)) else res
            self.test.assertIsInstance(FakeWork.unbox(work), FakeWork)

        return res