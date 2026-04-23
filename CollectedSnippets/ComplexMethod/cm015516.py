def _dist_train(
        self,
        with_nested_trunk,
        freezing_method,
        freeze_after_wrap_fsdp,
        with_fsdp,
        disable_autograd,
        forward_prefetch,
    ):
        torch.manual_seed(0)
        batch = torch.randn(size=(2, 3, 224, 224)).to(device_type)

        fsdp_kwargs = {
            "device_id": self.rank,
            "forward_prefetch": forward_prefetch,
        }

        ddp_kwargs = {
            "device_ids": [self.rank],
            "find_unused_parameters": bool(disable_autograd),
        }

        model = self._create_model(
            with_fsdp,
            with_nested_trunk,
            freeze_after_wrap_fsdp,
            disable_autograd,
            fsdp_kwargs,
        )
        model = model.to(device_type)

        # freezing the trunk using requires_grad.
        if freezing_method == FreezingMethod.RequiresGrad:
            for param in model.trunk.parameters():
                param.requires_grad = False

        if with_fsdp:
            if not freeze_after_wrap_fsdp:
                model.fsdp_wrap(fsdp_kwargs)
            model = FSDP(model, **fsdp_kwargs)
        else:
            model = DistributedDataParallel(model, **ddp_kwargs)

        target = torch.tensor([0, 1], dtype=torch.long).to(device_type)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.SGD(model.parameters(), lr=0.1, momentum=0.9)

        for _ in range(3):
            out = model(batch)
            fake_loss = criterion(out, target)
            optimizer.zero_grad()
            fake_loss.backward()
            if freezing_method == FreezingMethod.GradToNone:
                for param in model.module.trunk.parameters():
                    param.grad = None
            optimizer.step()

        if with_fsdp:
            return get_full_params(model)

        return list(model.parameters())