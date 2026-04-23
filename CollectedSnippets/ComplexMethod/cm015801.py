def test_augment_trace_against_flop_counter(self, device, dtype, maxat):
        # this tests to see if we can only use a Triton backend for max autotune
        max_autotune, backends = maxat
        if device == "cpu" or torch.version.hip is not None:
            return
        om = _test_model(device, dtype, compile=False)

        comp_omni = torch.compile(
            om,
            options={
                "benchmark_kernel": True,
                "max_autotune_gemm_backends": backends,
                "max_autotune": max_autotune,
            },
        )
        comp_omni()

        torch._dynamo.reset()  # reset the cache
        with fresh_inductor_cache():
            with torch.profiler.profile(record_shapes=True) as profile:
                comp_omni()

        torch._dynamo.reset()  # reset the cache
        with fresh_inductor_cache():
            with FlopCounterMode() as mode:
                comp_omni()

        trace1, trace2 = trace_files()
        profile.export_chrome_trace(trace1)
        with patch(
            "sys.argv",
            [*prefix, "--augment_trace", trace1, trace2, str(dtype).split(".")[-1]],
        ):
            main()

        with open(trace2) as f:
            out_profile = json.load(f)

        flop_counts = mode.flop_counts
        extern_mapping = _create_extern_mapping(out_profile)

        seen_mm = False
        seen_bmm = False
        seen_baddbmm = False
        seen_conv = False
        for event in out_profile["traceEvents"]:
            if (
                "cat" not in event
                or event["cat"] != "kernel"
                or "args" not in event
                or "External id" not in event["args"]
            ):
                continue

            external_op = extern_mapping[event["args"]["External id"]][0]
            name: str = external_op["name"]
            self.assertNotEqual(name, None)
            self.assertEqual(type(name), str)
            if name.startswith("aten::mm") or "_mm_" in name:
                seen_mm = True
                self.assertEqual(
                    event["args"]["kernel_flop"],
                    flop_counts["Global"][torch.ops.aten.mm],
                )
            if (
                name.startswith(
                    (
                        "aten::cudnn_convolution",
                        "aten::convolution",
                        "aten::_convolution",
                        "aten::convolution_overrideable",
                    )
                )
                or "conv" in name
            ):
                seen_conv = True
                self.assertEqual(
                    event["args"]["kernel_flop"],
                    flop_counts["Global"][torch.ops.aten.convolution],
                )
            if name.startswith("aten::baddbmm") or "_baddbmm_" in name:
                seen_baddbmm = True
                self.assertEqual(
                    event["args"]["kernel_flop"],
                    flop_counts["Global"][torch.ops.aten.baddbmm],
                )
            if name.startswith("aten::bmm") or "_bmm_" in name:
                seen_bmm = True
                self.assertEqual(
                    event["args"]["kernel_flop"],
                    flop_counts["Global"][torch.ops.aten.bmm],
                )
        self.assertTrue(seen_mm)
        self.assertTrue(seen_bmm)
        self.assertTrue(seen_baddbmm)
        self.assertTrue(seen_conv)