def test_fsdp_zero2_eval_with_prefetch(self):
        # Test FSDP validation with SHARD_GRAD_OP and forward_prefetch

        class Mnist(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv1 = nn.Conv2d(1, 32, 3, 1)
                self.conv2 = nn.Conv2d(32, 64, 3, 1)
                self.dropout1 = nn.Dropout(0.25)
                self.dropout2 = nn.Dropout(0.5)
                self.fc1 = nn.Linear(9216, 128)
                self.fc2 = nn.Linear(128, 10)
                self.ln = nn.LayerNorm(9216)

            def forward(self, x, y):
                x = self.conv1(x)
                x = torch.nn.functional.relu(x)
                x = self.conv2(x)
                x = torch.nn.functional.relu(x)
                x = torch.nn.functional.max_pool2d(x, 2)
                x = self.dropout1(x)
                x = torch.flatten(x, 1)
                x = self.ln(x)
                x = self.fc1(x)
                x = torch.nn.functional.relu(x)
                x = self.dropout2(x)
                x = self.fc2(x)
                output = torch.nn.functional.log_softmax(x, dim=1)
                loss = torch.nn.functional.cross_entropy(output, y)
                return loss

        model = Mnist().to(device=device_type)
        model1 = Mnist().to(device=device_type)
        model1.load_state_dict(model.state_dict())
        fsdp_model = FSDP(
            model,
            sharding_strategy=ShardingStrategy.SHARD_GRAD_OP,
            forward_prefetch=True,
            use_orig_params=True,
            auto_wrap_policy=ModuleWrapPolicy([nn.Linear, nn.Conv2d]),
        )
        ddp_model = torch.nn.parallel.DistributedDataParallel(
            model1,
        )

        fsdp_opt = torch.optim.SGD(fsdp_model.parameters(), lr=1e-4)
        ddp_opt = torch.optim.SGD(ddp_model.parameters(), lr=1e-4)

        seed = self.rank + 20231010
        torch.manual_seed(seed)
        torch.get_device_module(device_type).manual_seed(seed)

        losses = []
        grads = []
        for i in range(5):
            x = torch.randn(8, 1, 28, 28, device=device_type).requires_grad_()
            y = torch.randint(low=0, high=9, size=(8,), device=device_type)
            for model, opt in ((fsdp_model, fsdp_opt), (ddp_model, ddp_opt)):
                seed = self.rank + i
                torch.manual_seed(seed)
                torch.get_device_module(device_type).manual_seed(seed)
                loss = model(x, y).sum()
                losses.append(loss)
                loss.backward()
                opt.step()
                grads.append(x.grad)
                opt.zero_grad()
            if not torch.allclose(losses[0], losses[1]):
                raise AssertionError(
                    f"Expected losses to be close: {losses[0]} vs {losses[1]}"
                )
            if not torch.allclose(grads[0], grads[1]):
                raise AssertionError(
                    f"Expected grads to be close: {grads[0]} vs {grads[1]}"
                )
            losses.clear()
            grads.clear()

        with torch.no_grad():
            fsdp_model.eval()
            ddp_model.eval()
            for _ in range(5):
                x = torch.randn(8, 1, 28, 28, device=device_type).requires_grad_()
                y = torch.randint(low=0, high=9, size=(8,), device=device_type)
                fsdp_loss = fsdp_model(x, y)
                ddp_loss = ddp_model(x, y)
                if not torch.allclose(fsdp_loss, ddp_loss):
                    raise AssertionError(
                        f"Expected fsdp_loss and ddp_loss to be close: {fsdp_loss} vs {ddp_loss}"
                    )

        fsdp_model.train()
        ddp_model.train()
        for i in range(5):
            x = torch.randn(8, 1, 28, 28, device=device_type).requires_grad_()
            y = torch.randint(low=0, high=9, size=(8,), device=device_type)
            for model, opt in ((fsdp_model, fsdp_opt), (ddp_model, ddp_opt)):
                seed = self.rank + i
                torch.manual_seed(seed)
                torch.get_device_module(device_type).manual_seed(seed)
                loss = model(x, y).sum()
                losses.append(loss)
                loss.backward()
                opt.step()
                grads.append(x.grad)
                opt.zero_grad()
            if not torch.allclose(losses[0], losses[1]):
                raise AssertionError(
                    f"Expected losses to be close: {losses[0]} vs {losses[1]}"
                )
            if not torch.allclose(grads[0], grads[1]):
                raise AssertionError(
                    f"Expected grads to be close: {grads[0]} vs {grads[1]}"
                )
            losses.clear()
            grads.clear()