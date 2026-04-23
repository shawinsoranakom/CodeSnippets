def test_combine_profiles(self, device, dtype):
        """
        Test combining multiple profiles into a single profile.
        """
        if device == "cpu" or torch.version.hip is not None:
            return

        # Create three different models to generate different traces
        om1 = _test_model(device, dtype, addmm=True, bmm=False)
        om2 = _test_model(device, dtype, addmm=False, bmm=True)
        om3 = _pointwise_test_model(device, dtype)

        # Generate three separate traces
        trace1, trace2 = trace_files()
        trace3 = f"{TMP_DIR}/trace3-{uuid.uuid4()}.json"
        combined_trace = f"{TMP_DIR}/combined-{uuid.uuid4()}.json"

        # Generate first trace
        torch._dynamo.reset()
        with fresh_inductor_cache():
            with torch.profiler.profile(record_shapes=True) as p1:
                om1()
        p1.export_chrome_trace(trace1)

        # Generate second trace
        torch._dynamo.reset()
        with fresh_inductor_cache():
            with torch.profiler.profile(record_shapes=True) as p2:
                om2()
        p2.export_chrome_trace(trace2)

        # Generate third trace
        torch._dynamo.reset()
        with fresh_inductor_cache():
            with torch.profiler.profile(record_shapes=True) as p3:
                om3()
        p3.export_chrome_trace(trace3)

        # Combine the three traces
        with patch(
            "sys.argv",
            [
                *prefix,
                "--combine",
                trace1,
                trace2,
                trace3,
                combined_trace,
            ],
        ):
            main()

        # Verify the combined trace exists and contains expected data
        with open(combined_trace) as f:
            combined_profile = json.load(f)

        # Load original traces for comparison
        with open(trace1) as f:
            profile1 = json.load(f)
        with open(trace2) as f:
            profile2 = json.load(f)
        with open(trace3) as f:
            profile3 = json.load(f)

        # Verify trace events are combined
        expected_event_count = (
            len(profile1["traceEvents"])
            + len(profile2["traceEvents"])
            + len(profile3["traceEvents"])
        )
        self.assertEqual(len(combined_profile["traceEvents"]), expected_event_count)

        # Verify device properties are present
        self.assertIn("deviceProperties", combined_profile)
        # XPU currently does not have the deviceProperties like CUDA.
        # See https://github.com/intel/torch-xpu-ops/issues/2247
        if torch.cuda.is_available():
            self.assertGreater(len(combined_profile["deviceProperties"]), 0)

        # Verify some trace events from each original profile are present
        combined_event_names = {
            event["name"] for event in combined_profile["traceEvents"]
        }

        # Check that we have events from each original profile
        profile1_event_names = {event["name"] for event in profile1["traceEvents"]}
        profile2_event_names = {event["name"] for event in profile2["traceEvents"]}
        profile3_event_names = {event["name"] for event in profile3["traceEvents"]}

        # At least some events from each profile should be in the combined profile
        self.assertTrue(profile1_event_names.intersection(combined_event_names))
        self.assertTrue(profile2_event_names.intersection(combined_event_names))
        self.assertTrue(profile3_event_names.intersection(combined_event_names))