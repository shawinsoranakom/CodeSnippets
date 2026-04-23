def _test_post_acc_grad_hook_optim_parity(self, use_cpu_offload: bool):
        if use_cpu_offload and TEST_HPU:
            return  # pin_memory requires CUDA/XPU
        torch.manual_seed(42)
        model_args = ModelArgs(dropout_p=0.0)
        model = Transformer(model_args)

        offload_policy = CPUOffloadPolicy() if use_cpu_offload else OffloadPolicy()
        ref_model = copy.deepcopy(model).to(device_type)
        for module in itertools.chain(ref_model.layers, [ref_model]):
            fully_shard(module, offload_policy=offload_policy)
        optim_kwargs = {"lr": 1e-2, "foreach": False}
        ref_optim = torch.optim.AdamW(ref_model.parameters(), **optim_kwargs)
        lr_scheduler_kwargs = {"step_size": 5}
        ref_lr_scheduler = torch.optim.lr_scheduler.StepLR(
            ref_optim, **lr_scheduler_kwargs
        )

        for module in itertools.chain(model.layers, [model]):
            fully_shard(module, offload_policy=offload_policy)
        param_to_optim = {}
        param_to_lr_scheduler = {}
        for param in model.parameters():
            param_to_optim[param] = torch.optim.AdamW([param], **optim_kwargs)
            param_to_lr_scheduler[param] = torch.optim.lr_scheduler.StepLR(
                param_to_optim[param], **lr_scheduler_kwargs
            )

        def optim_hook(param: nn.Parameter) -> None:
            param_to_optim[param].step()
            param_to_optim[param].zero_grad()
            param_to_lr_scheduler[param].step()

        for param in model.parameters():
            param.register_post_accumulate_grad_hook(optim_hook)

        torch.manual_seed(42 + self.rank)
        inp = torch.randint(0, model_args.vocab_size, (2, 16), device=device_type)
        for _ in range(10):
            ref_loss = ref_model(inp).sum()
            ref_loss.backward()
            ref_optim.step()
            ref_optim.zero_grad()
            ref_lr_scheduler.step()
            loss = model(inp).sum()
            loss.backward()
            self.assertTrue(torch.equal(ref_loss, loss))
            for ref_param, param in zip(ref_model.parameters(), model.parameters()):
                self.assertTrue(torch.equal(ref_param, param))