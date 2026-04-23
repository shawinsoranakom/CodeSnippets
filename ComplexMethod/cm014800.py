def _generate_input(self, shape, dtype, device, with_extremal):
        if shape == ():
            x = torch.tensor((), dtype=dtype, device=device)
        else:
            if dtype.is_floating_point or dtype.is_complex:
                # work around torch.randn not being implemented for bfloat16
                if dtype == torch.bfloat16:
                    x = torch.randn(*shape, device=device) * random.randint(30, 100)
                    x = x.to(torch.bfloat16)
                else:
                    x = torch.randn(
                        *shape, dtype=dtype, device=device
                    ) * random.randint(30, 100)
                x[torch.randn(*shape) > 0.5] = 0
                if with_extremal and dtype.is_floating_point:
                    # Use extremal values
                    x[torch.randn(*shape) > 0.5] = float("nan")
                    x[torch.randn(*shape) > 0.5] = float("inf")
                    x[torch.randn(*shape) > 0.5] = float("-inf")
                elif with_extremal and dtype.is_complex:
                    x[torch.randn(*shape) > 0.5] = complex("nan")
                    x[torch.randn(*shape) > 0.5] = complex("inf")
                    x[torch.randn(*shape) > 0.5] = complex("-inf")
            elif dtype == torch.bool:
                x = torch.zeros(shape, dtype=dtype, device=device)
                x[torch.randn(*shape) > 0.5] = True
            else:
                x = torch.randint(15, 100, shape, dtype=dtype, device=device)

        return x