def test_update_inactive_constant_buffer_with_interleaved_folded_constants(self):
        if self.device == "mps":
            raise unittest.SkipTest("MPS baseline mismatch")

        class Model(torch.nn.Module):
            def __init__(self, device):
                super().__init__()
                self.fc1 = nn.Linear(2, 2, bias=True, device=device)
                self.post = nn.Linear(2, 2, bias=False, device=device)
                self.register_buffer(
                    "uie_user_memory_network",
                    torch.randn(2, 2, device=device),
                    persistent=True,
                )
                self.register_buffer(
                    "uie_item_memory_network",
                    torch.randn(2, 2, device=device),
                    persistent=True,
                )
                self.register_buffer(
                    "late_bias",
                    torch.randn(2, device=device),
                    persistent=True,
                )

            def forward(self, x):
                x = self.fc1(x)
                direct_user = torch.matmul(x, self.uie_user_memory_network)
                direct_item = torch.matmul(x, self.uie_item_memory_network)
                folded_user = torch.relu(self.uie_user_memory_network.permute(1, 0))
                folded_item = torch.relu(self.uie_item_memory_network.permute(1, 0))
                out = direct_user + direct_item
                out = out + torch.matmul(x, folded_user) + torch.matmul(x, folded_item)
                return self.post(out + self.late_bias)

        example_inputs = (torch.randn(2, 2, device=self.device),)
        with (
            torch.no_grad(),
            config.patch(
                {
                    "always_keep_tensor_constants": True,
                    "aot_inductor.use_runtime_constant_folding": True,
                }
            ),
        ):
            model = Model(self.device)
            so_path, _ = run_and_get_cpp_code(
                AOTIRunnerUtil.legacy_compile, model, example_inputs
            )

        runner = AOTIRunnerUtil.legacy_load_runner(self.device, so_path)
        name_to_fqn = runner.get_constant_names_to_original_fqns()
        self.assertTrue(
            [name for name in name_to_fqn if name.startswith("_FOLDED_CONST_")],
            msg="Expected runtime-folded constants in generated model",
        )

        def runner_call(x):
            return runner.run([x])[0]

        test_inputs = torch.tensor([[1.0, -2.0], [3.0, -4.0]], device=self.device)
        atol = 1e-3
        rtol = 1e-3
        expected = model(test_inputs)
        self.assertEqual(expected, runner_call(test_inputs), atol=atol, rtol=rtol)

        with torch.no_grad():
            for p in model.parameters():
                p.add_(1.0)
            for b in model.buffers():
                b.add_(2.0)

        state = {**dict(model.named_parameters()), **dict(model.named_buffers())}
        new_weights = {
            const_name: state[fqn].detach().clone()
            for const_name, fqn in name_to_fqn.items()
            if fqn in state
        }
        self.assertTrue(new_weights, msg="Expected non-empty constant update map")

        new_expected = model(test_inputs)

        runner.update_constant_buffer(new_weights, True, True)
        self.assertEqual(expected, runner_call(test_inputs), atol=atol, rtol=rtol)

        runner.swap_constant_buffer()
        self.assertEqual(new_expected, runner_call(test_inputs), atol=atol, rtol=rtol)