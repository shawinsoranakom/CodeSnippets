def test_cpu_load_state_dict(self, device, dtype, impl, optim_info):
        # NOTE: This SIMULATES a fused/capturable optimizer with state moved to CPU, issue 103256
        # How do we get there? Users typically create CUDA models on fused optimizers and then
        # store checkpoints on CPU as CUDA memory is limited with torch.load(...map_location="cpu").
        # Since this is a unit test, it is more expedient to simulate what the state_dict
        # would look like, which is basically CPU tensors with fused/capturable flag = True.
        optim_cls = optim_info.optim_cls
        opt_name = optim_cls.__name__
        if opt_name in ("SGD", "Adagrad") and impl == "capturable":
            # Capturable SGD/Adagrad does not exist
            self.skipTest(f"{opt_name} does not currently support capturable")
        if _get_device_type(device) == "cpu":
            self.skipTest("Test is only for non-cpu devices")
        elif (
            impl == "fused"
            and _get_device_type(device) not in optim_info.supports_fused_on
        ):
            self.skipTest(f"{device} is not supported for fused on {opt_name}")
        elif impl == "capturable" and _get_device_type(device) == "mps":
            self.skipTest("MPS does not support capturable")

        cpu_optim_inputs = optim_info.optim_inputs_func(device="cpu")
        for optim_input in cpu_optim_inputs:
            param = torch.tensor([0.1, 0.2], dtype=dtype, device="cpu")
            optimizer = optim_cls([param], **optim_input.kwargs)
            param.grad = torch.rand_like(param)
            optimizer.step()
            optim_state_dict_cpu = deepcopy(optimizer.state_dict())
            optim_state_dict_cpu["param_groups"][0][impl] = True

            # load
            optim_input.kwargs[impl] = True
            param_device = param.detach().clone().to(device=device)
            optimizer_device = optim_cls([param_device], **optim_input.kwargs)
            optimizer_device.load_state_dict(optim_state_dict_cpu)
            optimizer_device.zero_grad()
            param_device.grad = torch.rand_like(param_device)
            optimizer_device.step()