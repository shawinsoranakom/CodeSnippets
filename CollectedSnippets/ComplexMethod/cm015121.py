def test_unary_op_out_casting(self, device, dtypes):
        t = torch.tensor((1), dtype=dtypes[0], device=device)
        out = torch.empty(0, dtype=dtypes[1], device=device)

        ops = (torch.neg, torch.floor, torch.ceil)
        float_and_int_only_ops = {torch.floor, torch.ceil}
        real_only_ops = {torch.floor, torch.ceil}
        for op in ops:
            if dtypes[0] is not dtypes[1]:
                with self.assertRaises(RuntimeError):
                    op(t, out=out)
            elif op in real_only_ops and dtypes[0].is_complex:
                with self.assertRaises(RuntimeError):
                    op(t, out=out)
            elif (
                    op in float_and_int_only_ops
                    and (not dtypes[0].is_floating_point and not dtypes[0].is_complex)
                    and (not (dtypes[0] == torch.int64 and dtypes[1] == torch.int64))
                    and device != "meta"
            ):
                with self.assertRaises(RuntimeError):
                    op(t, out=out)
            else:
                self.assertEqual(op(t, out=out), op(t))
                self.assertEqual(op(t, out=out), out)