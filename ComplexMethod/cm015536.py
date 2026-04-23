def test_fsdp_optimizer_overlap(self):
        torch.manual_seed(0)
        for cpu_offload in [True, False]:
            offload = CPUOffload(offload_params=cpu_offload)
            model = MyModel().to(device=device_type)
            model_overlap = deepcopy(model)
            fsdp = FSDP(
                model.to(device=device_type),
                auto_wrap_policy=always_wrap_policy,
                use_orig_params=True,
                cpu_offload=offload,
            )
            fsdp_overlap = FSDP(
                model_overlap.to(device=device_type),
                auto_wrap_policy=always_wrap_policy,
                use_orig_params=True,
                cpu_offload=offload,
            )
            optim_cls = torch.optim.SGD
            optim_kwargs = {"lr": 0.03}
            _apply_optimizer_in_backward(
                optimizer_class=optim_cls,
                params=fsdp_overlap.parameters(),
                optimizer_kwargs=optim_kwargs,
                register_hook=False,
            )
            for p in fsdp_overlap.parameters():
                if not hasattr(p, "_in_backward_optimizers"):
                    raise AssertionError(
                        "Expected parameter to have '_in_backward_optimizers' attribute"
                    )
            optim = optim_cls(fsdp.parameters(), **optim_kwargs)

            # Verify params initially equal
            for p1, p2 in zip(fsdp.parameters(), fsdp_overlap.parameters()):
                self.assertEqual(p1, p2)

            with FSDP.summon_full_params(fsdp_overlap):
                fsdp_overlap_prev_params = [
                    (n, p.clone()) for n, p in fsdp_overlap.named_parameters()
                ]

            for i in range(6):
                inp = torch.randn(2, 2, device=device_type)
                with torch.no_grad():
                    inp_clone = inp.clone()
                fsdp(inp, inp).sum().backward()
                fsdp_overlap(inp_clone, inp_clone).sum().backward()

                optim.step()
                optim.zero_grad()

                # Overlapped optimizer FSDP module should have sharded_grad as None.
                for fsdp_unit in FSDP.fsdp_modules(fsdp_overlap):
                    handle = fsdp_unit._handle
                    if handle:
                        handle_grad = handle.sharded_grad
                        self.assertEqual(
                            None,
                            handle_grad,
                            "Overlapped FSDP sharded_grad is not None!",
                        )

                # Note: FSDP without optimizer overlap won't set sharded_grad to None until the next
                # pre-forward since it needs to run FSDP specific logic that picks up that set_to_none=True
                # has been called (or that the gradients have been otherwise set to None)

                # Verify parameters are different than prev iteration
                with FSDP.summon_full_params(fsdp_overlap, with_grads=True):
                    for (n, p), (n_prev, p_prev) in zip(
                        fsdp_overlap.named_parameters(), fsdp_overlap_prev_params
                    ):
                        self.assertEqual(n, n_prev)
                        self.assertNotEqual(
                            p,
                            p_prev,
                            f"{n_prev} Params at iter {i} same as previous iter!",
                        )

                # Verify overlap and non overlapped are the same
                with FSDP.summon_full_params(fsdp_overlap):
                    with FSDP.summon_full_params(fsdp):
                        for (n_overlap, p_overlap), (n, p) in zip(
                            fsdp_overlap.named_parameters(), fsdp.named_parameters()
                        ):
                            self.assertEqual(n_overlap, n)
                            self.assertEqual(
                                p,
                                p_overlap,
                                f"Rank {self.rank}: Params not equal at iteration {i}: {n_overlap} - {p} vs {p_overlap}",
                            )
                            self.assertEqual(
                                None, p.grad, f"Expected param {n} grad to be None"
                            )
                            self.assertEqual(
                                None,
                                p_overlap.grad,
                                f"Expected param {n_overlap} grad to be None",
                            )

                    fsdp_overlap_prev_params = [
                        (n, p.clone()) for n, p in fsdp_overlap.named_parameters()
                    ]