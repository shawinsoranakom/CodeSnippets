def test_combo_kernel_coordesc_tunes_largest_subkernel_first(self):
        def fn(a, b, c):
            return (
                torch.nn.functional.relu(a),
                torch.nn.functional.sigmoid(b),
                torch.nn.functional.tanh(c),
            )

        inps = [
            torch.rand(32, 1024, device=GPU_TYPE),
            torch.rand(256, 256, device=GPU_TYPE),
            torch.rand(16, 128, device=GPU_TYPE),
        ]

        out_eager = fn(*inps)

        def parse_block_cfg(msg: str) -> dict[str, int]:
            return {
                m.group(1): int(m.group(2))
                for m in re.finditer(r"(\w+BLOCK_\d+): (\d+)", msg)
            }

        logger = logging.getLogger("torch._inductor.runtime.coordinate_descent_tuner")
        with torch._inductor.config.patch(coordinate_descent_tuning=True):
            with self.assertLogs(logger, level=logging.DEBUG) as cm:
                out_compiled = torch.compile(fn)(*inps)

        self.assertEqual(out_eager, out_compiled)

        baseline_log = next(
            msg for msg in cm.output if "Baseline Config" in msg and "XBLOCK_" in msg
        )
        baseline_cfg = parse_block_cfg(baseline_log)
        try_logs = [
            msg for msg in cm.output if "Try config" in msg and "XBLOCK_" in msg
        ]
        self.assertGreater(
            len(try_logs), 0, "Coordinate descent did not try combo fields"
        )
        distinct_block_cfgs = {
            tuple(sorted(parse_block_cfg(msg).items())) for msg in try_logs
        }
        self.assertGreater(
            len(distinct_block_cfgs),
            1,
            "Coordinate descent did not explore different suffixed block sizes.",
        )

        first_cfg = parse_block_cfg(try_logs[0])
        changed_fields = {
            key for key, value in first_cfg.items() if baseline_cfg.get(key) != value
        }
        self.assertEqual(
            changed_fields,
            {"XBLOCK_1"},
            f"Expected the first combo coordesc step to tune the largest subkernel first, got {changed_fields}",
        )