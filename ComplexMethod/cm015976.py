def test_datapipe_with_record_function(self):
        with _profile(
            with_stack=True, use_kineto=kineto_available(), record_shapes=True
        ) as prof:
            input_dp1 = dp.iter.IterableWrapper(range(4))
            input_dp2 = dp.iter.IterableWrapper(range(4, 8))
            input_dp3 = dp.iter.IterableWrapper(range(8, 12))
            output_dp = input_dp1.mux(input_dp2, input_dp3)
            output = list(output_dp)

        has_iter = False
        has_mux = False
        for e in prof.function_events:
            if has_iter and has_mux:
                break

            if not has_iter and "IterableWrapper" in e.name:
                has_iter = True
            if not has_mux and "Multiplexer" in e.name:
                has_mux = True
        self.assertTrue(has_iter)
        self.assertTrue(has_mux)