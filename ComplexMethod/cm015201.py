def test_scan_dtype(self, reverse, compile_mode, device, dtype):
        scan_fct = compile_mode_helper(scan, compile_mode)

        # Check all outputs and carries on the correct device and with torch.float32
        x = torch.randn(3, 10, 2, device=device).to(dtype=dtype)
        op, init = (
            get_scan_combine_fn("adds"),
            torch.zeros(10, 2, device=device, dtype=dtype),
        )
        result = scan_fct(op, init, x, dim=0, reverse=reverse)
        result_exp = _fake_scan(op, init=init, xs=x, dim=0, reverse=reverse)
        self.assertEqual(result, result_exp)
        self.assertEqual(
            [[r.device.type for r in res] for res in result],
            [[device.type for _ in res] for res in result],
        )
        self.assertEqual(
            [[r.dtype for r in res] for res in result],
            [[dtype for _ in res] for res in result],
        )

        # Check all outputs and carries on the correct device and
        # carry.dtype torch.float32 and output.dtype torch.float16
        x = torch.randn(3, 10, 2, device=device).to(dtype=dtype)
        op, init = (
            get_scan_combine_fn("adds"),
            torch.zeros(10, 2, device=device, dtype=torch.float32),
        )
        result = scan_fct(op, init, x, dim=0, reverse=reverse)
        result_exp = _fake_scan(op, init=init, xs=x, dim=0, reverse=reverse)
        self.assertEqual(result, result_exp)
        self.assertEqual(
            [[r.dtype for r in res] for res in result],
            [
                [torch.float32 for _ in range(len(result[0]))],
                [dtype for _ in range(len(result[1]))],
            ],
        )

        # Check all outputs and carries on the correct device and
        # carry.dtype torch.int64 and output.dtype torch.float32
        x = torch.randn(3, 10, 2, device=device)
        op, init = (
            get_scan_combine_fn("adds"),
            torch.zeros(10, 2, device=device, dtype=dtype),
        )
        result = scan_fct(op, init, x, dim=0, reverse=reverse)
        result_exp = _fake_scan(op, init=init, xs=x, dim=0, reverse=reverse)
        self.assertEqual(result, result_exp)
        self.assertEqual(
            [[r.dtype for r in res] for res in result],
            [
                [dtype for _ in range(len(result[0]))],
                [torch.float32 for _ in range(len(result[1]))],
            ],
        )