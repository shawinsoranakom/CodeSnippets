def test_load_state_dict_assign_meta(self, keep_vars):
        class MyModule(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.fc1 = nn.Linear(3, 5)
                self.bn = nn.BatchNorm1d(5)
                self.x = nn.Parameter(torch.rand(5), requires_grad=False)

            def forward(self, input):
                return self.x + self.bn(self.fc1(input))

        swap = torch.__future__.get_swap_module_params_on_conversion()
        net = MyModule()
        state_dict = net.state_dict(keep_vars=keep_vars)
        for v in state_dict.values():
            v.requires_grad_(False)

        with torch.device("meta"):
            net_meta = MyModule()

        net_meta_state_dict_old = net_meta.state_dict(keep_vars=True)
        net_meta.load_state_dict(state_dict, assign=True)

        # Make sure parameters and persistent buffers were assigned
        net_meta_state_dict = net_meta.state_dict(keep_vars=True)
        for key in state_dict:
            if key in net_meta._parameters:
                if keep_vars and not swap:
                    # state_dict[key] is an nn.Parameter
                    self.assertTrue(state_dict[key] is net_meta_state_dict[key])
                else:
                    if swap:
                        self.assertTrue(
                            net_meta_state_dict[key] is net_meta_state_dict_old[key]
                        )
                    else:
                        # state_dict[key] is not an nn.Parameter so it will be detached when wrapping with a Parameter
                        self.assertTrue(
                            net_meta_state_dict[key] is not net_meta_state_dict_old[key]
                        )
                        self.assertEqual(
                            net_meta_state_dict_old[key].requires_grad,
                            net_meta_state_dict[key].requires_grad,
                        )
                self.assertEqual(
                    net_meta_state_dict_old[key].requires_grad,
                    net_meta_state_dict[key].requires_grad,
                )
                self.assertEqual(state_dict[key], net_meta_state_dict[key])
            elif (
                key in net_meta._buffers
                and key not in net_meta._non_persistent_buffers_set
            ):
                self.assertTrue(state_dict[key] is net_meta_state_dict[key])
                self.assertEqual(state_dict[key], net_meta_state_dict[key])

        # Make sure that ordering of parameters and buffers is preserved
        net_named_parameters = net.named_parameters()
        net_named_buffers = net.named_buffers()
        net_meta_named_parameters = net_meta.named_parameters()
        net_meta_named_buffers = net_meta.named_buffers()

        for (n1, _), (n2, _) in zip(net_named_parameters, net_meta_named_parameters):
            self.assertEqual(n1, n2)

        for (n1, _), (n2, _) in zip(net_named_buffers, net_meta_named_buffers):
            self.assertEqual(n1, n2)

        # Make sure outputs are the same
        t = torch.randn(4, 3)
        out_net = net(t)
        out_net_meta = net_meta(t.clone())

        self.assertEqual(out_net, out_net_meta)