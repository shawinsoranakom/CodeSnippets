def test_honor_sm_carveout(self) -> None:
        torch.manual_seed(42)

        x = torch.randn(8192, 2048, device="cuda", dtype=torch.float32)
        y = torch.randn(8192, 2048, device="cuda", dtype=torch.float32).t()
        x_scales = tensor_to_scale(x, e4m3_type, dim=1).reciprocal()
        y_scales = tensor_to_scale(y, e4m3_type, dim=0).reciprocal()
        x_fp8 = to_fp8_saturated(x / x_scales, e4m3_type)
        y_fp8 = to_fp8_saturated(y / y_scales, e4m3_type)

        cu_count = torch.cuda.get_device_properties().multi_processor_count
        carveout = 66 if torch.version.cuda else cu_count // 8

        with tempfile.NamedTemporaryFile() as f:
            with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CUDA]) as prof:
                self.assertIsNone(torch._C._get_sm_carveout_experimental())
                scaled_mm_wrap(x_fp8, y_fp8, scale_a=x_scales, scale_b=y_scales, out_dtype=torch.bfloat16)
                torch._C._set_sm_carveout_experimental(0)
                self.assertEqual(torch._C._get_sm_carveout_experimental(), 0)
                scaled_mm_wrap(x_fp8, y_fp8, scale_a=x_scales, scale_b=y_scales, out_dtype=torch.bfloat16)
                torch._C._set_sm_carveout_experimental(66)
                self.assertEqual(torch._C._get_sm_carveout_experimental(), 66)
                scaled_mm_wrap(x_fp8, y_fp8, scale_a=x_scales, scale_b=y_scales, out_dtype=torch.bfloat16)
                torch._C._set_sm_carveout_experimental(None)
                self.assertIsNone(torch._C._get_sm_carveout_experimental())
                scaled_mm_wrap(x_fp8, y_fp8, scale_a=x_scales, scale_b=y_scales, out_dtype=torch.bfloat16)

            prof.export_chrome_trace(f.name)
            if torch.version.hip:
                with open(f.name) as file:
                    events = [evt for evt in json.load(file)["traceEvents"] if evt.get("cat", "") == "kernel"]
                # events were returned out of order; need to be sorted on "ts" timestamp
                events = sorted(events, key=lambda x: x['ts'])
                # ROCm carveout is invisible except for kernels running slower on fewer CUs
                no_carveout, carveout_0, carveout, no_carveout_again = [float(evt.get("dur", "0.0")) for evt in events]
                if True or not (no_carveout < carveout and carveout_0 < carveout and no_carveout_again < carveout):  # noqa: SIM222
                    # something went wrong, print more info to help debug flaky test
                    print("ROCm debug info for test_honor_sm_carveout")
                    print("cu_count", cu_count)
                    print("no_carveout", no_carveout)
                    print("carveout_0", carveout_0)
                    print("carveout", carveout)
                    print("no_carveout_again", no_carveout_again)
                self.assertTrue(no_carveout < carveout)
                self.assertTrue(carveout_0 < carveout)
                self.assertTrue(no_carveout_again < carveout)
                # ROCm carveout will create new streams when enabled, and go back to the original stream when disabled
                no_carveout, carveout_0, carveout, no_carveout_again = [int(evt.get("tid", "0")) for evt in events]
                self.assertTrue(no_carveout == no_carveout_again)
                self.assertTrue(no_carveout == carveout_0)
                self.assertTrue(no_carveout != carveout)
                self.assertTrue(carveout_0 != carveout)
            else:
                with open(f.name) as file:
                    no_carveout, carveout_0, carveout_66, no_carveout_again = [
                        math.prod(evt.get("args", {}).get("grid", []))
                        for evt in json.load(file)["traceEvents"]
                        if evt.get("cat", "") == "kernel"
                    ]

                self.assertEqual(no_carveout, no_carveout_again)
                capability = torch.cuda.get_device_capability()
                if capability in {(10, 0), (10, 3), (11, 0), (12, 0), (12, 1)}:
                    # expected failure
                    # CUTLASS only supports SM carveout via green contexts on SM100
                    self.assertEqual(no_carveout, carveout_66)
                    self.assertEqual(carveout_66, carveout_0)
                else:
                    # correct behavior
                    self.assertNotEqual(no_carveout, carveout_66)
                    self.assertNotEqual(carveout_66, carveout_0)