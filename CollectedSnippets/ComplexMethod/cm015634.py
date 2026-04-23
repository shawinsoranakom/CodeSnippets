def test_numpy_torch_operators(self):
        def fn(op, t1, t2):
            return op(t1, t2)

        from torch._dynamo.variables.builtin import BuiltinVariable

        operators = BuiltinVariable._fx_graph_functions()

        for op, t1_np, t2_np in itertools.product(
            operators, (True, False), (True, False)
        ):
            if op in [operator.eq, operator.ne]:
                # returns equivalent of torch.eq/ne
                continue
            if op is operator.getitem:
                # skip
                # Did you know that tensor[ndarray_of_floats] works?
                continue
            if op is operator.imatmul and (t1_np or t2_np):
                # skip
                # in numpy, in place matmul does not work single
                # dimensional arrays
                continue
            t1 = torch.rand(5)
            if t1_np:
                t1 = t1.numpy()
            t2 = torch.rand(5)
            if t2_np:
                t2 = t2.numpy()
            try:
                # TODO try a bit harder
                result = op(t1, t2)
            except (RuntimeError, TypeError, IndexError):
                continue
            cnts = torch._dynamo.testing.CompileCounter()
            opt_fn = torch.compile(fn, backend=cnts)
            self.assertEqual(result, opt_fn(op, t1, t2), msg=f"{op=} {t1_np=} {t2_np=}")
            self.assertEqual(cnts.frame_count, 1, msg=f"{op=} {t1_np=} {t2_np=}")
            torch._dynamo.reset()