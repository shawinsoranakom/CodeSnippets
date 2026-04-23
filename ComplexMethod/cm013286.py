def _test_ddp_apply_optim_in_backward(
            self,
            optim_cls,
            optim_kwargs,
            init_before,
            gradient_as_bucket_view=True,
        ):
            # Need to seed to ensure inputs are unique across rank. Otherwise,
            # allreduce won't have any effect.
            torch.manual_seed(self.rank)
            torch.cuda.manual_seed(self.rank)
            torch.cuda.set_device(self.rank)

            # Test a simple linear as well as a ResNet model.
            models_to_test = [
                nn.Sequential(nn.Linear(3, 3), nn.Linear(3, 3), nn.Linear(3, 3)).cuda(),
                # run model of at least 1M parameters to hit potential race conditions in
                # stream semantics
                nn.Sequential(
                    nn.Linear(3, 1024), nn.Linear(1024, 1024), nn.Linear(1024, 3)
                ).cuda(),
            ]
            if HAS_TORCHVISION:
                models_to_test.append(torchvision.models.resnet50().cuda())

            for j, model in enumerate(models_to_test):
                model_optim_in_bwd = copy.deepcopy(model)
                model = nn.parallel.DistributedDataParallel(
                    model,
                    device_ids=[self.rank],
                    gradient_as_bucket_view=gradient_as_bucket_view,
                )
                optim = optim_cls(model.parameters(), **optim_kwargs)
                if init_before:
                    _apply_optimizer_in_backward(
                        optimizer_class=optim_cls,
                        params=model_optim_in_bwd.parameters(),
                        optimizer_kwargs=optim_kwargs,
                    )
                model_optim_in_bwd = nn.parallel.DistributedDataParallel(
                    model_optim_in_bwd,
                    device_ids=[self.rank],
                    gradient_as_bucket_view=gradient_as_bucket_view,
                )
                if not init_before:
                    _apply_optimizer_in_backward(
                        optimizer_class=optim_cls,
                        params=model_optim_in_bwd.parameters(),
                        optimizer_kwargs=optim_kwargs,
                    )

                for p1, p2 in zip(
                    model.parameters(), model_optim_in_bwd.parameters(), strict=True
                ):
                    self.assertEqual(p1, p2, "Parameters not initially equal!")
                # Enable determinism in cudnn operators
                with torch.backends.cudnn.flags(
                    enabled=True, deterministic=True, benchmark=False
                ):
                    for i in range(8):
                        inp = (
                            torch.randn(1, 3, 1000, 1000, device="cuda")
                            if j == 2
                            else torch.randn(10, 3, device="cuda")
                        )
                        model(inp).sum().backward()
                        optim.step()
                        model_optim_in_bwd(
                            inp
                        ).sum().backward()  # runs optimizer as well
                        for p1, p2 in zip(
                            model.parameters(),
                            model_optim_in_bwd.parameters(),
                            strict=True,
                        ):
                            self.assertEqual(
                                p1, p2, f"Params not equal at iteration {i}"
                            )
                            self.assertTrue(
                                p2.grad is None,
                                f"Optim in backward grad is not None at {i}",
                            )

                        # set_to_none for regular optimizer to match in backward
                        # case.
                        optim.zero_grad(set_to_none=True)