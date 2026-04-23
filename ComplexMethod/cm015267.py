def test_insert_quant_dequant_shared_class_type(self):
        class M(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv1 = torch.nn.Conv2d(3, 3, 3).float()
                self.conv2 = torch.nn.Conv2d(3, 3, 3).float()

            def forward(self, x):
                return self.conv2(self.conv1(x))

        for is_per_channel in [True, False]:
            m = torch.jit.script(M())
            observer = (
                default_per_channel_weight_observer.with_args(ch_axis=1)
                if is_per_channel
                else default_observer
            )
            qconfig = QConfig(activation=observer, weight=observer)
            qconfig_dict = {"": qconfig}
            m = prepare_jit(m, qconfig_dict)
            # observers for input, output and value between conv1/conv2
            if len(attrs_with_prefix(m, "_observer_")) != 3:
                raise AssertionError("Expected to have 3 observers")
            # observer for weight
            if len(attrs_with_prefix(m.conv1, "_observer_")) != 1:
                raise AssertionError("Expected to have 1 observers")
            # observer for weight
            if len(attrs_with_prefix(m.conv2, "_observer_")) != 1:
                raise AssertionError("Expected to have 1 observers")

            data = torch.randn(1, 3, 10, 10, dtype=torch.float)
            m(data)
            m = convert_jit(m, debug=True)
            m(data)
            if m.conv1._c._type() != m.conv2._c._type():
                raise AssertionError(
                    f"Expected conv1 and conv2 to share the same type, "
                    f"got {m.conv1._c._type()} and {m.conv2._c._type()}"
                )

            # check all observers have been removed
            if len(attrs_with_prefix(m, "_observer_")) != 0:
                raise AssertionError("Expected to have 0 observers")
            if len(attrs_with_prefix(m.conv1, "_observer_")) != 0:
                raise AssertionError("Expected to have 0 observers")
            if len(attrs_with_prefix(m.conv2, "_observer_")) != 0:
                raise AssertionError("Expected to have 0 observers")

            quant_func = (
                "aten::quantize_per_channel"
                if is_per_channel
                else "aten::quantize_per_tensor"
            )
            for module in ["conv1", "conv2"]:
                conv = m._c.getattr(module)
                # quantize weight
                FileCheck().check(quant_func).check_next("aten::dequantize").check(
                    'prim::CallMethod[name="_conv_forward"]'
                ).check("return").run(get_forward_graph(conv))
                # no quantize node in _conv_forward
                FileCheck().check_not(quant_func).check("aten::conv2d").check_not(
                    quant_func
                ).check("return").run(conv._get_method("_conv_forward").graph)