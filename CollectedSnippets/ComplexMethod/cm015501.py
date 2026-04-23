def _test_grad_writeback(
        self,
        change_first_weight_grad: bool,
        change_data: bool,
        set_to_none: bool,
    ):
        if change_data and set_to_none:
            return  # not well-defined

        def transform_grad(param: nn.Parameter) -> nn.Parameter:
            return None if set_to_none else torch.ones_like(param) * 2

        ddp_model = DDP(
            TestFSDPUseOrigParamsWriteback.Model(torch.device(device_type)),
            device_ids=[self.rank],
        )
        fsdp_model = FSDP(
            TestFSDPUseOrigParamsWriteback.Model(torch.device(device_type)),
            use_orig_params=True,
        )
        LR = 1e-2
        # TODO: If we add `summon_full_params(with_grads=True)`, then replace
        # the following. For now, we use the optimizer step as a surrogate for
        # checking that gradients were written back.
        ddp_optim = torch.optim.Adam(ddp_model.parameters(), lr=LR)
        fsdp_optim = torch.optim.Adam(fsdp_model.parameters(), lr=LR)

        # Generate an initial gradient
        inp = fsdp_model.get_input(torch.device(device_type))
        ddp_out = ddp_model(*inp)
        fsdp_out = fsdp_model(*inp)
        ddp_out.sum().backward()
        fsdp_out.sum().backward()

        # Change the gradient through the original parameters
        ddp = ddp_model.module  # for brevity
        fsdp = fsdp_model.module
        if change_first_weight_grad:
            if change_data:
                ddp.lin1.weight.grad.data = transform_grad(ddp.lin1.weight)
                if fsdp.lin1.weight.grad is not None:
                    fsdp.lin1.weight.grad.data = transform_grad(fsdp.lin1.weight)
            else:
                ddp.lin1.weight.grad = transform_grad(ddp.lin1.weight)
                fsdp.lin1.weight.grad = transform_grad(fsdp.lin1.weight)
        else:
            if change_data:
                ddp.lin2.weight.grad.data = transform_grad(ddp.lin2.weight)
                if fsdp.lin2.weight.grad is not None:
                    fsdp.lin2.weight.grad.data = transform_grad(fsdp.lin2.weight)
            else:
                ddp.lin2.weight.grad = transform_grad(ddp.lin2.weight)
                fsdp.lin2.weight.grad = transform_grad(fsdp.lin2.weight)
        ddp_optim.step()
        fsdp_optim.step()
        self._check_param_parity(ddp_model, fsdp_model)  # triggers a writeback

        # Intentionally do not zero the gradient to check writeback
        inp = fsdp_model.get_input(torch.device(device_type))
        ddp_out = ddp_model(*inp)
        fsdp_out = fsdp_model(*inp)
        ddp_out.sum().backward()
        fsdp_out.sum().backward()
        ddp_optim.step()
        fsdp_optim.step()
        self._check_param_parity(ddp_model, fsdp_model)