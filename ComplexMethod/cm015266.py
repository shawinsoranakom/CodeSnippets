def test_insert_observers_for_if_consistent_observation(self):
        """check quantization for if works as long as
        output of all branches are quantized/observed consistently
        """

        class M(torch.nn.Module):
            def __init__(self, cond):
                super().__init__()
                self.conv = torch.nn.Conv2d(3, 3, 3).float()
                self.cond = cond

            def forward(self, x):
                x = self.conv(x)
                # x is already observed
                if self.cond:
                    x = torch.flatten(x)
                return x

        class M2(torch.nn.Module):
            def __init__(self, cond):
                super().__init__()
                self.conv1 = torch.nn.Conv2d(3, 3, 3).float()
                self.conv2 = torch.nn.Conv2d(3, 3, 3).float()
                self.cond = cond

            def forward(self, x):
                x = self.conv1(x)
                if self.cond:
                    x = self.conv2(x)
                    # x will be observed in the branch
                else:
                    x = torch.flatten(x)
                # since output for both branch are quantized
                # the if node is quantized consistently
                return x

        data = torch.rand((1, 3, 5, 5), dtype=torch.float)
        options = list(itertools.product([True, False], [True, False]))
        for cond, tracing in options:
            if tracing:
                m = torch.jit.trace(M(cond), data)
            else:
                m = torch.jit.script(M(cond))
            m = prepare_jit(m, {"": default_qconfig})
            if len(attrs_with_prefix(m, "_observer_")) != 2:
                raise AssertionError(
                    f"Expected 2 observers, got {len(attrs_with_prefix(m, '_observer_'))}"
                )

        for cond, tracing in options:
            if tracing:
                m = torch.jit.trace(M2(cond), data)
            else:
                m = torch.jit.script(M2(cond))
            m = prepare_jit(m, {"": default_qconfig})
            num_observers = 2 if tracing and not cond else 3
            if len(attrs_with_prefix(m, "_observer_")) != num_observers:
                raise AssertionError(
                    f"Expected {num_observers} observers, "
                    f"got {len(attrs_with_prefix(m, '_observer_'))}"
                )