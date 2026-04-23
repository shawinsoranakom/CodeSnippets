def test_datapipe_with_record_function_fork(self):
        with _profile(
            with_stack=True, use_kineto=kineto_available(), record_shapes=True
        ) as prof:
            input_dp = dp.iter.IterableWrapper(range(10))
            dp1, dp2, dp3 = input_dp.fork(num_instances=3)
            output1 = list(dp1)
        has_iter = False
        has_child = False
        for e in prof.function_events:
            if has_iter and has_child:
                break

            if not has_iter and "IterableWrapper" in e.name:
                has_iter = True
            if not has_child and "_ChildDataPipe" in e.name:
                has_child = True
        self.assertTrue(has_iter)
        self.assertTrue(has_child)