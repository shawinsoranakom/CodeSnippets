def test_insert_observers_weight_dtype(self):
        class M(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv = torch.nn.Conv2d(3, 5, 3)

            def forward(self, x):
                return F.relu(self.conv(x))

        m = torch.jit.script(M())
        qconfig_dict = {"": default_qconfig}
        m = prepare_jit(m, qconfig_dict)
        activation_dtypes = {
            obs.getattr("dtype")
            for x, obs in m._modules._c.items()
            if x.startswith("_observer_")
        }
        weight_dtypes = {
            obs.getattr("dtype")
            for x, obs in m.conv._modules._c.items()
            if x.startswith("_observer_")
        }
        if len(activation_dtypes) != 1:
            raise AssertionError("Expected to have 1 activation dtype")
        if len(weight_dtypes) != 1:
            raise AssertionError("Expected to have 1 weight dtype")
        if next(iter(activation_dtypes)) == next(iter(weight_dtypes)):
            raise AssertionError("Expected activation dtype to ")
        " be different from wegiht dtype"