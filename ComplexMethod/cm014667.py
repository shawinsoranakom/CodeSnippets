def test_demux_iterdatapipe(self):
        input_dp = dp.iter.IterableWrapper(range(10))

        with self.assertRaises(ValueError):
            input_dp.demux(num_instances=0, classifier_fn=lambda x: 0)

        # Functional Test: split into 2 DataPipes and output them one at a time
        dp1, dp2 = input_dp.demux(num_instances=2, classifier_fn=lambda x: x % 2)
        output1, output2 = list(dp1), list(dp2)
        self.assertEqual(list(range(0, 10, 2)), output1)
        self.assertEqual(list(range(1, 10, 2)), output2)

        # Functional Test: split into 2 DataPipes and output them together
        dp1, dp2 = input_dp.demux(num_instances=2, classifier_fn=lambda x: x % 2)
        output = []
        for n1, n2 in zip(dp1, dp2):
            output.append((n1, n2))
        self.assertEqual([(i, i + 1) for i in range(0, 10, 2)], output)

        # Functional Test: values of the same classification are lumped together, and buffer_size = 3 being too small
        dp1, dp2 = input_dp.demux(
            num_instances=2, classifier_fn=lambda x: 0 if x >= 5 else 1, buffer_size=4
        )
        it1 = iter(dp1)
        with self.assertRaises(BufferError):
            next(
                it1
            )  # Buffer raises because first 5 elements all belong to the a different child
        with self.assertRaises(BufferError):
            list(dp2)

        # Functional Test: values of the same classification are lumped together, and buffer_size = 5 is just enough
        dp1, dp2 = input_dp.demux(
            num_instances=2, classifier_fn=lambda x: 0 if x >= 5 else 1, buffer_size=5
        )
        output1, output2 = list(dp1), list(dp2)
        self.assertEqual(list(range(5, 10)), output1)
        self.assertEqual(list(range(5)), output2)

        # Functional Test: values of the same classification are lumped together, and unlimited buffer
        with warnings.catch_warnings(record=True) as wa:
            dp1, dp2 = input_dp.demux(
                num_instances=2,
                classifier_fn=lambda x: 0 if x >= 5 else 1,
                buffer_size=-1,
            )
            exp_l = 1 if HAS_DILL else 2
            self.assertEqual(len(wa), exp_l)
            self.assertRegex(str(wa[-1].message), r"Unlimited buffer size is set")
        output1, output2 = list(dp1), list(dp2)
        self.assertEqual(list(range(5, 10)), output1)
        self.assertEqual(list(range(5)), output2)

        # Functional Test: classifier returns a value outside of [0, num_instance - 1]
        dp0 = input_dp.demux(num_instances=1, classifier_fn=lambda x: x % 2)
        it = iter(dp0[0])
        with self.assertRaises(ValueError):
            next(it)
            next(it)

        # Reset Test: DataPipe resets when a new iterator is created, even if this datapipe hasn't been read
        dp1, dp2 = input_dp.demux(num_instances=2, classifier_fn=lambda x: x % 2)
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
        self.assertEqual(list(range(1, 10, 2)), output2)

        # Reset Test: DataPipe resets when some of it has been read
        dp1, dp2 = input_dp.demux(num_instances=2, classifier_fn=lambda x: x % 2)
        output1, output2 = [], []
        for n1, n2 in zip(dp1, dp2):
            output1.append(n1)
            output2.append(n2)
            if n1 == 4:
                break
        with warnings.catch_warnings(record=True) as wa:
            iter(dp1)  # Reset all child DataPipes
            self.assertEqual(len(wa), 1)
            self.assertRegex(
                str(wa[0].message), r"Some child DataPipes are not exhausted"
            )
            for n1, n2 in zip(dp1, dp2):
                output1.append(n1)
                output2.append(n2)
            self.assertEqual([0, 2, 4] + list(range(0, 10, 2)), output1)
            self.assertEqual([1, 3, 5] + list(range(1, 10, 2)), output2)
            self.assertEqual(len(wa), 1)
            self.assertRegex(str(wa[0].message), r"child DataPipes are not exhausted")

        # Reset Test: DataPipe reset, even when not all child DataPipes are exhausted
        dp1, dp2 = input_dp.demux(num_instances=2, classifier_fn=lambda x: x % 2)
        output1 = list(dp1)
        self.assertEqual(list(range(0, 10, 2)), output1)
        with warnings.catch_warnings(record=True) as wa:
            self.assertEqual(
                list(range(0, 10, 2)), list(dp1)
            )  # Reset even when dp2 is not read
            self.assertEqual(len(wa), 1)
            self.assertRegex(
                str(wa[0].message), r"Some child DataPipes are not exhausted"
            )
        output2 = []
        for i, n2 in enumerate(dp2):
            output2.append(n2)
            if i == 1:
                self.assertEqual(list(range(1, 5, 2)), output2)
                with warnings.catch_warnings(record=True) as wa:
                    self.assertEqual(
                        list(range(0, 10, 2)), list(dp1)
                    )  # Can reset even when dp2 is partially read
                    self.assertEqual(len(wa), 1)
                    self.assertRegex(
                        str(wa[0].message), r"Some child DataPipes are not exhausted"
                    )
                break
        output2 = list(dp2)  # output2 has to read from beginning again
        self.assertEqual(list(range(1, 10, 2)), output2)

        # Functional Test: drop_none = True
        dp1, dp2 = input_dp.demux(
            num_instances=2,
            classifier_fn=lambda x: x % 2 if x % 5 != 0 else None,
            drop_none=True,
        )
        self.assertEqual([2, 4, 6, 8], list(dp1))
        self.assertEqual([1, 3, 7, 9], list(dp2))

        # Functional Test: drop_none = False
        dp1, dp2 = input_dp.demux(
            num_instances=2,
            classifier_fn=lambda x: x % 2 if x % 5 != 0 else None,
            drop_none=False,
        )
        it1 = iter(dp1)
        with self.assertRaises(ValueError):
            next(it1)

        # __len__ Test: __len__ not implemented
        dp1, dp2 = input_dp.demux(num_instances=2, classifier_fn=lambda x: x % 2)
        with self.assertRaises(TypeError):
            len(
                dp1
            )  # It is not implemented as we do not know length for each child in advance
        with self.assertRaises(TypeError):
            len(dp2)

        # Pickle Test:
        dp1, dp2 = input_dp.demux(num_instances=2, classifier_fn=odd_or_even)
        traverse_dps(dp1)  # This should not raise any error
        for _ in zip(dp1, dp2):
            pass
        traverse_dps(dp2)