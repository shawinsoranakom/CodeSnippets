def _test_to_empty_and_reset_parameters(
        self, model: nn.Module, mesh: DeviceMesh, mlp_dim: int
    ):
        # Check that we can materialize it on GPU with empty values
        device = torch.device(
            device_type.type, torch.get_device_module(device_type).current_device()
        )
        model.to_empty(device=device)
        for param in model.parameters():
            self.assertEqual(param.device, device)
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)

        # Check that `reset_parameters()` on each module initializes values
        const = 1337
        for tensor in itertools.chain(model.parameters(), model.buffers()):
            tensor.detach().fill_(const)
        for module in model.modules():
            if hasattr(module, "reset_parameters"):
                module.reset_parameters()
        for param in model.parameters():
            local_tensor = param.to_local()
            if local_tensor.numel() > 0:
                self.assertNotEqual(local_tensor, torch.ones_like(local_tensor) * const)
        for buffer in model.buffers():
            self.assertNotEqual(buffer, torch.ones_like(buffer) * const)

        # Check that we can run an iteration without erroring
        inp = torch.randn((4, mlp_dim), device=device_type.type)
        model(inp).sum().backward()
        optim.step()