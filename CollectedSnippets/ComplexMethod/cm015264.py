def test_insert_observers_skip_values(self):
        class ConvFunctionalReLU(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv = torch.nn.Conv2d(3, 5, 3)

            def forward(self, x):
                return F.relu(self.conv(x))

        class ConvReLUModule(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv = torch.nn.Conv2d(3, 5, 3)
                self.relu = torch.nn.ReLU()

            def forward(self, x):
                return self.relu(self.conv(x))

        class AddReLUModule(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.relu = torch.nn.ReLU()
                self.conv = torch.nn.Conv2d(3, 3, 3).float()

            def forward(self, x):
                out = self.conv(x)
                out += x
                return self.relu(out)

        class AddFunctionalReLU(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv = torch.nn.Conv2d(3, 3, 3).float()

            def forward(self, x):
                out = self.conv(x)
                out += x
                return F.relu(out)

        def attrs_with_prefix(module, prefix):
            return [x for x, _ in module._modules._c.items() if x.startswith(prefix)]

        qconfig_dict = {"": default_qconfig}
        m = torch.jit.script(ConvFunctionalReLU())
        m = prepare_jit(m, qconfig_dict)
        # observer for weight of conv
        if len(attrs_with_prefix(m.conv, "_observer_")) != 1:
            raise AssertionError(
                f"Expected 1 observer, got {len(attrs_with_prefix(m.conv, '_observer_'))}"
            )
        # observer for input of conv and output of relu
        if len(attrs_with_prefix(m, "_observer_")) != 2:
            raise AssertionError(
                f"Expected 2 observers, got {len(attrs_with_prefix(m, '_observer_'))}"
            )

        m = torch.jit.script(ConvReLUModule())
        m = prepare_jit(m, qconfig_dict)
        # observer for input of conv and output of relu
        if len(attrs_with_prefix(m, "_observer_")) != 2:
            raise AssertionError(
                f"Expected 2 observers, got {len(attrs_with_prefix(m, '_observer_'))}"
            )
        # observer for weight of conv
        if len(attrs_with_prefix(m.conv, "_observer_")) != 1:
            raise AssertionError(
                f"Expected 1 observer, got {len(attrs_with_prefix(m.conv, '_observer_'))}"
            )
        # observer for output of relu
        if len(attrs_with_prefix(m.relu, "_observer_")) != 0:
            raise AssertionError(
                f"Expected 0 observers, got {len(attrs_with_prefix(m.relu, '_observer_'))}"
            )

        m = torch.jit.script(AddReLUModule())
        qconfig_dict = {"": default_qconfig}
        m = prepare_jit(m, qconfig_dict)
        if len(attrs_with_prefix(m, "_observer")) != 3:
            raise AssertionError(
                f"Expected 3 observers, got {len(attrs_with_prefix(m, '_observer'))}"
            )
        if len(attrs_with_prefix(m.relu, "_observer")) != 0:
            raise AssertionError(
                f"Expected 0 observers, got {len(attrs_with_prefix(m.relu, '_observer'))}"
            )
        FileCheck().check("aten::add_").check_not(
            'Observer = prim::GetAttr[name="_observer_'
        ).check("ReLU = prim::GetAttr").run(str(get_forward_graph(m._c)))

        m = torch.jit.script(AddFunctionalReLU())
        qconfig_dict = {"": default_qconfig}
        m = prepare_jit(m, qconfig_dict)
        if len(attrs_with_prefix(m, "_observer")) != 3:
            raise AssertionError(
                f"Expected 3 observers, got {len(attrs_with_prefix(m, '_observer'))}"
            )
        FileCheck().check("aten::add_").check_not(
            'Observer = prim::GetAttr[name="_observer_'
        ).check("CallFunction").check('Observer = prim::GetAttr[name="_observer_').run(
            str(get_forward_graph(m._c))
        )