def test_ddp_mixed_real_and_complex_params(self):
        # test ddp with mixed real and complex parameters and gradients
        process_group = self._get_process_group()
        device_id = gpus_for_rank(self.world_size)[self.rank][0]
        device = torch.device(f"cuda:{device_id}")

        class MixedModule(nn.Module):
            def __init__(self):
                super().__init__()
                self.complex_fc = nn.Linear(4, 4, dtype=torch.cfloat)
                self.real_fc = nn.Linear(4, 4, dtype=torch.float32)
                self.final_fc = nn.Linear(4, 2, dtype=torch.cfloat)

            def forward(self, x_complex, x_real):
                complex_branch = self.complex_fc(x_complex)
                real_branch = self.real_fc(x_real)
                real_as_complex = torch.complex(
                    real_branch, torch.zeros_like(real_branch)
                )
                return self.final_fc(complex_branch + real_as_complex)

        torch.manual_seed(42 + self.rank)
        model = MixedModule().to(device)
        ref_model = MixedModule().to(device)

        # 100 forces large bucket, forcing the BucketKey mechanism to segregate buckets, testing bucket segregation by dtype
        ddp_model = DistributedDataParallel(
            model,
            device_ids=[device_id],
            process_group=process_group,
            bucket_cap_mb=100,
        )

        optimizer_ddp = torch.optim.SGD(ddp_model.parameters(), lr=0.01)
        optimizer_ref = torch.optim.SGD(ref_model.parameters(), lr=0.01)

        torch.manual_seed(100)
        x_complex = torch.randn(8, 4, dtype=torch.cfloat, device=device)
        x_real = torch.randn(8, 4, dtype=torch.float32, device=device)
        target = torch.randn(8, 2, dtype=torch.cfloat, device=device)

        for iteration in range(5):
            optimizer_ddp.zero_grad()
            loss_ddp = torch.mean(torch.abs(ddp_model(x_complex, x_real) - target) ** 2)
            loss_ddp.backward()

            optimizer_ref.zero_grad()
            with torch.no_grad():
                for p_ddp, p_ref in zip(ddp_model.parameters(), ref_model.parameters()):
                    p_ref.copy_(p_ddp)
            loss_ref = torch.mean(torch.abs(ref_model(x_complex, x_real) - target) ** 2)
            loss_ref.backward()
            for param in ref_model.parameters(5):
                if param.grad is not None and param.grad.is_floating_point():
                    dist.all_reduce(
                        param.grad.data,
                        op=dist.ReduceOp.SUM,
                        group=process_group,
                    )
                    param.grad.data /= self.world_size

            for name, (p_ddp, p_ref) in enumerate(
                zip(ddp_model.parameters(), ref_model.parameters())
            ):
                self.assertIsNotNone(
                    p_ddp.grad,
                    f"DDP gradient is None at iteration {iteration}, param {name}",
                )
                self.assertIsNotNone(
                    p_ref.grad,
                    f"Reference gradient is None at iteration {iteration}, param {name}",
                )

                self.assertTrue(
                    p_ddp.grad.is_complex() == p_ref.grad.is_complex(),
                    f"Gradient dtype mismatch at iteration {iteration}, param {name}",
                )

                if p_ddp.grad.is_complex():
                    self.assertFalse(
                        torch.allclose(
                            p_ddp.grad.imag, torch.zeros_like(p_ddp.grad.imag)
                        ),
                        f"DDP imaginary gradient is all zeros at iteration {iteration}, param {name}",
                    )
                    self.assertTrue(
                        torch.allclose(
                            p_ddp.grad.real, p_ref.grad.real, rtol=1e-5, atol=1e-5
                        ),
                        f"Real gradient mismatch at iteration {iteration}, param {name}",
                    )
                    self.assertTrue(
                        torch.allclose(
                            p_ddp.grad.imag, p_ref.grad.imag, rtol=1e-5, atol=1e-5
                        ),
                        f"Imaginary gradient mismatch at iteration {iteration}, param {name}",
                    )
                else:
                    self.assertTrue(
                        torch.allclose(p_ddp.grad, p_ref.grad, rtol=1e-5, atol=1e-5),
                        f"Real gradient mismatch at iteration {iteration}, param {name}",
                    )