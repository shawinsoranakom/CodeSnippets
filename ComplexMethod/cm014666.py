def test_fork_iterdatapipe(self):
        input_dp = dp.iter.IterableWrapper(range(10))

        with self.assertRaises(ValueError):
            input_dp.fork(num_instances=0)

        dp0 = input_dp.fork(num_instances=1, buffer_size=0)
        self.assertEqual(dp0, input_dp)

        # Functional Test: making sure all child DataPipe shares the same reference
        dp1, dp2, dp3 = input_dp.fork(num_instances=3)
        self.assertTrue(all(n1 is n2 and n1 is n3 for n1, n2, n3 in zip(dp1, dp2, dp3)))

        # Functional Test: one child DataPipe yields all value at a time
        output1, output2, output3 = list(dp1), list(dp2), list(dp3)
        self.assertEqual(list(range(10)), output1)
        self.assertEqual(list(range(10)), output2)
        self.assertEqual(list(range(10)), output3)

        # Functional Test: two child DataPipes yield value together
        dp1, dp2 = input_dp.fork(num_instances=2)
        output = []
        for n1, n2 in zip(dp1, dp2):
            output.append((n1, n2))
        self.assertEqual([(i, i) for i in range(10)], output)

        # Functional Test: one child DataPipe yields all value first, but buffer_size = 5 being too small
        dp1, dp2 = input_dp.fork(num_instances=2, buffer_size=4)
        it1 = iter(dp1)
        for _ in range(4):
            next(it1)
        with self.assertRaises(BufferError):
            next(it1)
        with self.assertRaises(BufferError):
            list(dp2)

        dp1, dp2 = input_dp.fork(num_instances=2, buffer_size=5)
        with self.assertRaises(BufferError):
            list(dp2)

        # Functional Test: one child DataPipe yields all value first with unlimited buffer
        with warnings.catch_warnings(record=True) as wa:
            dp1, dp2 = input_dp.fork(num_instances=2, buffer_size=-1)
            self.assertEqual(len(wa), 1)
            self.assertRegex(str(wa[0].message), r"Unlimited buffer size is set")
        l1, l2 = list(dp1), list(dp2)
        for d1, d2 in zip(l1, l2):
            self.assertEqual(d1, d2)

        # Functional Test: two child DataPipes yield value together with buffer size 1
        dp1, dp2 = input_dp.fork(num_instances=2, buffer_size=1)
        output = []
        for n1, n2 in zip(dp1, dp2):
            output.append((n1, n2))
        self.assertEqual([(i, i) for i in range(10)], output)

        # Functional Test: two child DataPipes yield shallow copies with copy equals shallow
        dp1, dp2 = input_dp.map(_to_list).fork(num_instances=2, copy="shallow")
        for n1, n2 in zip(dp1, dp2):
            self.assertIsNot(n1, n2)
            self.assertEqual(n1, n2)

        # Functional Test: two child DataPipes yield deep copies with copy equals deep
        dp1, dp2 = (
            input_dp.map(_to_list).map(_to_list).fork(num_instances=2, copy="deep")
        )
        for n1, n2 in zip(dp1, dp2):
            self.assertIsNot(n1[0], n2[0])
            self.assertEqual(n1, n2)

        # Functional Test: fork DataPipe raises error for unknown copy method
        with self.assertRaises(ValueError):
            input_dp.fork(num_instances=2, copy="unknown")

        # Functional Test: make sure logic related to slowest_ptr is working properly
        dp1, dp2, dp3 = input_dp.fork(num_instances=3)
        output1, output2, output3 = [], [], []
        for i, (n1, n2) in enumerate(zip(dp1, dp2)):
            output1.append(n1)
            output2.append(n2)
            if i == 4:  # yield all of dp3 when halfway through dp1, dp2
                output3 = list(dp3)
                break
        self.assertEqual(list(range(5)), output1)
        self.assertEqual(list(range(5)), output2)
        self.assertEqual(list(range(10)), output3)

        # Reset Test: DataPipe resets when a new iterator is created, even if this datapipe hasn't been read
        dp1, dp2 = input_dp.fork(num_instances=2)
        _ = iter(dp1)
        output2 = []
        with self.assertRaisesRegex(RuntimeError, r"iterator has been invalidated"):
            for i, n2 in enumerate(dp2):
                output2.append(n2)
                if i == 4:
                    with warnings.catch_warnings(record=True) as wa:
                        _ = iter(dp1)  # This will reset all child DataPipes
                        self.assertEqual(len(wa), 1)
                        self.assertRegex(
                            str(wa[0].message), r"child DataPipes are not exhausted"
                        )
        self.assertEqual(list(range(5)), output2)

        # Reset Test: DataPipe resets when some of it has been read
        dp1, dp2 = input_dp.fork(num_instances=2)
        output1, output2 = [], []
        for i, (n1, n2) in enumerate(zip(dp1, dp2)):
            output1.append(n1)
            output2.append(n2)
            if i == 4:
                with warnings.catch_warnings(record=True) as wa:
                    _ = iter(dp1)  # Reset both all child DataPipe
                    self.assertEqual(len(wa), 1)
                    self.assertRegex(
                        str(wa[0].message), r"Some child DataPipes are not exhausted"
                    )
                break
        with warnings.catch_warnings(record=True) as wa:
            for n1, n2 in zip(dp1, dp2):
                output1.append(n1)
                output2.append(n2)
            self.assertEqual(len(wa), 1)
            self.assertRegex(str(wa[0].message), r"child DataPipes are not exhausted")
        self.assertEqual(list(range(5)) + list(range(10)), output1)
        self.assertEqual(list(range(5)) + list(range(10)), output2)

        # Reset Test: DataPipe reset, even when some other child DataPipes are not read
        dp1, dp2, dp3 = input_dp.fork(num_instances=3)
        output1, output2 = list(dp1), list(dp2)
        self.assertEqual(list(range(10)), output1)
        self.assertEqual(list(range(10)), output2)
        with warnings.catch_warnings(record=True) as wa:
            self.assertEqual(
                list(range(10)), list(dp1)
            )  # Resets even though dp3 has not been read
            self.assertEqual(len(wa), 1)
            self.assertRegex(
                str(wa[0].message), r"Some child DataPipes are not exhausted"
            )
        output3 = []
        for i, n3 in enumerate(dp3):
            output3.append(n3)
            if i == 4:
                with warnings.catch_warnings(record=True) as wa:
                    output1 = list(dp1)  # Resets even though dp3 is only partially read
                    self.assertEqual(len(wa), 1)
                    self.assertRegex(
                        str(wa[0].message), r"Some child DataPipes are not exhausted"
                    )
                self.assertEqual(list(range(5)), output3)
                self.assertEqual(list(range(10)), output1)
                break
        self.assertEqual(
            list(range(10)), list(dp3)
        )  # dp3 has to read from the start again

        # __len__ Test: Each DataPipe inherits the source datapipe's length
        dp1, dp2, dp3 = input_dp.fork(num_instances=3)
        self.assertEqual(len(input_dp), len(dp1))
        self.assertEqual(len(input_dp), len(dp2))
        self.assertEqual(len(input_dp), len(dp3))

        # Pickle Test:
        dp1, dp2, dp3 = input_dp.fork(num_instances=3)
        traverse_dps(dp1)  # This should not raise any error
        for _ in zip(dp1, dp2, dp3):
            pass
        traverse_dps(dp2)