def test_binary_ops_with_scalars(self, device):
        for python_op, torch_op in (
            (operator.add, torch.add),
            (operator.sub, torch.sub),
            (operator.mul, torch.mul),
            (operator.truediv, torch.div),
        ):
            for a, b in product(range(-10, 10), range(-10, 10)):
                for op in (lambda x: x * 0.5, lambda x: math.floor(x)):
                    a = op(a)
                    b = op(b)

                    # Skips zero divisors
                    if b == 0 or a == 0:
                        continue

                    a_tensor = torch.tensor(a, device=device)
                    b_tensor = torch.tensor(b, device=device)
                    a_tensor_cpu = a_tensor.cpu()
                    b_tensor_cpu = b_tensor.cpu()
                    vals = (a, b, a_tensor, b_tensor, a_tensor_cpu, b_tensor_cpu)

                    for args in product(vals, vals):
                        first, second = args

                        first_scalar = (
                            first
                            if not isinstance(first, torch.Tensor)
                            else first.item()
                        )
                        second_scalar = (
                            second
                            if not isinstance(second, torch.Tensor)
                            else second.item()
                        )
                        expected = python_op(first_scalar, second_scalar)

                        self.assertEqual(expected, python_op(first, second))
                        self.assertEqual(expected, torch_op(first, second))