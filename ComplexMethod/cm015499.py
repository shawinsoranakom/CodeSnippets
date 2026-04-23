def _check_train_parity(
        self,
        ddp_model: DDP,
        ddp_optim: torch.optim.Optimizer,
        fsdp_model: FSDP,
        fsdp_optim: torch.optim.Optimizer,
        set_to_none: bool,
        num_iters: int = 10,
    ):
        """Checks training parity between DDP and FSDP."""
        device = torch.device(device_type)
        for i in range(num_iters):
            iter_losses = []
            for model, optim in ((ddp_model, ddp_optim), (fsdp_model, fsdp_optim)):
                module = model.module
                # Test two different `zero_grad()` timings
                if i % 2 == 0:
                    optim.zero_grad(set_to_none=set_to_none)  # pre-forward
                inp = module.get_input(device)
                output = model(*inp)
                loss = module.get_loss(inp, output).to(device)
                iter_losses.append(loss)
                if i % 2 == 1:
                    optim.zero_grad(set_to_none=set_to_none)  # pre-backward
                module.run_backward(loss)
                # Perform the DDP optimizer step on CPU to match FSDP if needed
                if model is ddp_model and fsdp_model.cpu_offload.offload_params:
                    model.to(torch.device("cpu"))
                optim.step()
                if model is ddp_model and fsdp_model.cpu_offload.offload_params:
                    model.to(device)
            torch.testing.assert_close(iter_losses[0], iter_losses[1])
            iter_losses.clear()
        self._check_ddp_fsdp_param_parity(ddp_model, fsdp_model)