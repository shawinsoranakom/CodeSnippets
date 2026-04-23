def test_constructor(self):
        """Check the robustness of the ZeroRedundancyOptimizer constructor by
        passing different values for the ``params`` argument."""
        self.create_pg(self.device)
        LR = 0.01
        m = torch.nn.Sequential(
            torch.nn.Linear(5, 10),
            torch.nn.Linear(10, 10),
            torch.nn.Linear(10, 10),
        )
        # Test various constructor inputs in the form: (input, expected error)
        ctor_inputs = [
            ([], ValueError),  # empty parameter list
            (torch.randn(1), TypeError),  # non-iterable: `torch.Tensor`
            (1.2, TypeError),  # non-iterable: `float`
            (
                [
                    {"params": [l.weight for l in m]},
                    {"params": [l.bias for l in m]},
                ],
                None,
            ),  # iterable of dict
            (
                list(m.parameters()) + [42],
                TypeError,
            ),  # iterable containing invalid type
            (m.parameters(), None),  # `params` as a generator
            (list(m.parameters()), None),  # `params` as a list
        ]
        for ctor_input, error in ctor_inputs:
            context = self.assertRaises(error) if error else nullcontext()
            with context:
                ZeroRedundancyOptimizer(
                    ctor_input,
                    optimizer_class=SGD,
                    lr=LR,
                )

        # Test constructing with multiple parameter groups more thoroughly
        WD = 0.01
        BETAS = (0.9, 0.999)
        EPS = 1e-8
        params = [
            {"params": [l.weight for l in m], "weight_decay": 0.0},
            {"params": [l.bias for l in m], "weight_decay": WD},
        ]
        o = ZeroRedundancyOptimizer(
            params,
            optimizer_class=AdamW,
            lr=LR,
            betas=BETAS,
            eps=EPS,
        )
        if not (len(o.param_groups) == 2):
            raise AssertionError(
                f"Expected 2 ZeRO param groups, but got {len(o.param_groups)}"
            )
        if not (len(o.optim.param_groups) == 2):
            raise AssertionError(
                "Expected 2 local optimizer param groups, but got "
                f"{len(o.optim.param_groups)}"
            )