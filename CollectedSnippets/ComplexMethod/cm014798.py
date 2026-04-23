def test_div_and_floordiv_script_vs_python(self, device):
        # Creates jitted functions of two tensors
        def _wrapped_div(a, b):
            return a / b

        def _wrapped_floordiv(a, b):
            return a // b

        scripted_div = torch.jit.script(_wrapped_div)
        scripted_floordiv = torch.jit.script(_wrapped_floordiv)
        for a, b in product(range(-10, 10), range(-10, 10)):
            for op in (lambda x: x * 0.5, lambda x: math.floor(x)):
                a = op(a)
                b = op(b)

                # Skips zero divisors
                if b == 0:
                    continue

                expected_div = a / b
                expected_floordiv = math.floor(a / b)
                a_t = torch.tensor(a, device=device)
                b_t = torch.tensor(b, device=device)

                self.assertEqual(scripted_div(a_t, b_t), expected_div)
                self.assertEqual(scripted_floordiv(a_t, b_t), expected_floordiv)

        # Creates jitted functions of one tensor
        def _wrapped_div_scalar(a):
            return a / 5

        # NOTE: the JIT implements division as torch.reciprocal(a) * 5
        def _wrapped_rdiv_scalar(a):
            return 5 / a

        def _wrapped_floordiv_scalar(a):
            return a // 5

        # NOTE: this fails if the input is not an integer tensor
        # See https://github.com/pytorch/pytorch/issues/45199
        def _wrapped_rfloordiv_scalar(a):
            return 5 // a

        scripted_div_scalar = torch.jit.script(_wrapped_div_scalar)
        scripted_rdiv_scalar = torch.jit.script(_wrapped_rdiv_scalar)
        scripted_floordiv_scalar = torch.jit.script(_wrapped_floordiv_scalar)
        scripted_rfloordiv_scalar = torch.jit.script(_wrapped_rfloordiv_scalar)

        for a in range(-10, 10):
            for op in (lambda x: x * 0.5, lambda x: math.floor(x)):
                a = op(a)

                a_t = torch.tensor(a, device=device)

                self.assertEqual(a / 5, scripted_div_scalar(a_t))

                # Skips zero divisors
                if a == 0:
                    continue

                self.assertEqual(5 / a, scripted_rdiv_scalar(a_t))

                # Handles Issue 45199 (see comment above)
                if a_t.is_floating_point():
                    with self.assertRaises(RuntimeError):
                        scripted_rfloordiv_scalar(a_t)
                else:
                    # This should emit a UserWarning, why doesn't it?
                    # See issue gh-52387
                    self.assertEqual(5 // a, scripted_rfloordiv_scalar(a_t))