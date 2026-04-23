def test_tensor_print(self, device, op_list_data):
        op_list, shapes = op_list_data

        for dt in get_all_fp_dtypes():
            data = [torch.randn(s, dtype=dt, device=device) for s in shapes]

            for x in data:
                buf = None

                def foo(t):
                    nonlocal buf
                    buf = repr(t)
                    return t.mean()

                fn = foo
                bdim = 0
                for op in reversed(op_list):
                    if op is vmap:
                        fn = op(fn, in_dims=bdim)
                        bdim += 1
                    else:
                        fn = op(fn)

                expected = f"{repr(x)}"
                for level, op in enumerate(op_list):
                    if op is grad:
                        expected = (
                            f"GradTrackingTensor(lvl={level + 1}, value={expected})"
                        )
                    elif op is vmap:
                        bdim -= 1
                        expected = f"BatchedTensor(lvl={level + 1}, bdim={bdim}, value={expected})"

                fn(x)
                buf = buf.replace("\n", "").replace("  ", "")
                expected = expected.replace("\n", "").replace("  ", "")
                self.assertEqual(expected, buf)