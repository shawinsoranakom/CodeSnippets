def _test_clip_grad_norm(
        self,
        max_norm: float | int,
        norm_type: float | int,
        ref_model: nn.Module,
        ref_optim: torch.optim.Optimizer,
        model: nn.Module,
        optim: torch.optim.Optimizer,
        inp: torch.Tensor,
        dp_mesh: DeviceMesh | None = None,
    ):
        vector_norm_fn = functools.partial(torch.linalg.vector_norm, ord=norm_type)
        dp_mesh = dp_mesh or init_device_mesh(device_type.type, (self.world_size,))
        torch.manual_seed(42 + dp_mesh.get_local_rank() + 1)
        for _ in range(10):
            ref_optim.zero_grad()
            ref_model(inp).sum().backward()
            optim.zero_grad()
            model(inp).sum().backward()

            ref_grads = [p.grad.detach().clone() for p in ref_model.parameters()]
            local_grads = [
                p.grad.to_local().detach().clone() for p in model.parameters()
            ]
            for ref_grad, param in zip(ref_grads, model.parameters()):
                self.assertEqual(ref_grad, param.grad.full_tensor())

            # Check that at least one gradient has norm greater than the max
            # norm before clipping to ensure the clipping is not vacuous
            self.assertTrue(any(vector_norm_fn(g).item() > max_norm for g in ref_grads))
            self.assertTrue(
                any(vector_norm_fn(g).item() > max_norm for g in local_grads)
            )

            # Check gradient norm clipping via total norm and individual
            # gradient norms post-clipping
            ref_total_norm = torch.nn.utils.clip_grad_norm_(
                ref_model.parameters(), max_norm=max_norm, norm_type=norm_type
            )
            comm_mode = CommDebugMode()
            with comm_mode:
                # foreach is default to turn on so we don't need to specify it.
                total_norm = torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    max_norm=max_norm,
                    norm_type=norm_type,
                )
            self.assertEqual(ref_total_norm, total_norm.full_tensor())
            # Expect one all-reduce per mesh dim for partial -> replicate
            expected_all_reduces = len(total_norm.placements)
            self.assertEqual(
                comm_mode.get_comm_counts()[torch.ops.c10d_functional.all_reduce],
                expected_all_reduces,
            )
            # For zero gradients, clipping has no effect
            for param, grad in zip(ref_model.parameters(), ref_grads):
                self.assertTrue(vector_norm_fn(param.grad).item() <= max_norm)
                if torch.count_nonzero(grad):
                    self.assertFalse(torch.equal(param.grad, grad))
            for param, grad in zip(model.parameters(), local_grads):
                self.assertTrue(
                    vector_norm_fn(param.grad.to_local()).item() <= max_norm
                )
                if torch.count_nonzero(grad):
                    self.assertFalse(torch.equal(param.grad.to_local(), grad))