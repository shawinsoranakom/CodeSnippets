def _test_zero_join(self, device):
        """Check that the ZeRO join hook allows training with uneven inputs
        when using the given device."""
        NUM_INPUTS = 3
        NUM_EPOCHS = 2
        LR = 0.01
        torch.manual_seed(0)
        if "cpu" not in device:
            torch.get_device_module(device).manual_seed(0)

        rank = self.rank
        world_size = self.world_size
        self.create_pg(device)

        model = torch.nn.Sequential(
            torch.nn.Linear(2, 3),
            torch.nn.Linear(3, 3),
            torch.nn.Linear(3, 3),
        )
        model.to(device)

        # DDP ensures correct gradients in data parallel training, so DDP with
        # local optimizers on uneven inputs should be equivalent to ZeRO on
        # uneven inputs with gradients being manually set
        ddp_model = (
            DDP(model, device_ids=[rank]) if requires_ddp_rank(device) else DDP(model)
        )
        local_optim = torch.optim.Adam(ddp_model.parameters(), lr=LR)
        zero_model = copy.deepcopy(model)
        zero_model.to(device)
        zero_optim = ZeroRedundancyOptimizer(
            zero_model.parameters(),
            torch.optim.Adam,
            lr=LR,
        )
        loss_fn = torch.nn.MSELoss()

        # Use uneven inputs: rank i has i extra inputs
        inputs = [torch.randn(20, 2).to(device) for _ in range(NUM_INPUTS + rank)]
        labels = torch.randn(20, 3).to(device)

        # Save the gradients and parameters from DDP as the ground truth; do
        # so on the last-joining rank (in this case, the largest rank)
        grads_at_each_iter = []
        params_at_each_iter = []
        with ddp_model.join():
            for _ in range(NUM_EPOCHS):
                for input in inputs:
                    output = ddp_model(input)
                    loss_fn(output, labels).backward()
                    if rank == world_size - 1:
                        grads = []
                        for p in ddp_model.parameters():
                            grads.append(p.grad.detach().clone().to(device))
                    local_optim.step()
                    if rank == world_size - 1:
                        params = []
                        for p in ddp_model.parameters():
                            params.append(p.detach().clone().to(device))
                        grads_at_each_iter.append(grads)
                        params_at_each_iter.append(params)

        # Broadcast the saved gradients and parameters to all of the other
        # ranks (which joined early)
        grads_and_params = [grads_at_each_iter, params_at_each_iter]
        grads_and_params = _broadcast_object(
            grads_and_params,
            src_rank=world_size - 1,
            group=dist.group.WORLD,
            device=device,
        )
        grads_at_each_iter = grads_and_params[0]
        params_at_each_iter = grads_and_params[1]
        # TODO: Replace this `_broadcast_object` with `broadcast_object_list`
        # once the latter supports loading to the destination device instead
        # of the source device

        # A process must still set the remaining gradients after joining, so we
        # define a join hook to do this before the ZeRO join hook
        class _JoinGradInfo:
            def __init__(self, grads):
                self.grads = grads  # remaining gradients to set (in order)
                self.index = 0

        class _SetGradsJoinHook(JoinHook):
            def __init__(self, zero_optim, grads):
                zero_optim._join_grad_info = _JoinGradInfo(grads)
                self.zero = zero_optim
                super().__init__()

            def main_hook(self):
                join_grad_info = self.zero._join_grad_info
                grads = self.zero._join_grad_info.grads[join_grad_info.index]
                join_grad_info.index += 1
                for p, grad in zip(self.zero._all_params, grads):
                    p.grad = grad.detach().clone().to(device)

        class _GradientSetter(Joinable):
            def __init__(self) -> None:
                super().__init__()

            def join_hook(self, **kwargs):
                if "zero_optim" not in kwargs:
                    raise AssertionError("Expected 'zero_optim' in kwargs")
                if "grads" not in kwargs:
                    raise AssertionError("Expected 'grads' in kwargs")
                zero_optim = kwargs["zero_optim"]
                grads = kwargs["grads"]
                return _SetGradsJoinHook(zero_optim, grads)

            @property
            def join_device(self):
                return device

            @property
            def join_process_group(self):
                return dist.group.WORLD

        num_grads_after_joining = NUM_EPOCHS * (world_size - rank - 1)
        grads = grads_at_each_iter[-num_grads_after_joining:]
        gradient_setter = _GradientSetter()
        iter = 0
        with Join(
            [gradient_setter, zero_optim],
            zero_optim=zero_optim,
            grads=grads,
        ):
            for _ in range(NUM_EPOCHS):
                for _input in inputs:
                    # Notify join context that this process has not joined
                    Join.notify_join_context(gradient_setter)
                    # Set gradients manually
                    for p, grad in zip(
                        zero_model.parameters(),
                        grads_at_each_iter[iter],
                    ):
                        p.grad = grad.detach().clone().to(device)
                    # Perform optimizer step and check parity
                    zero_optim.step()
                    for p, ddp_p in zip(
                        zero_model.parameters(),
                        params_at_each_iter[iter],
                    ):
                        torch.testing.assert_close(
                            p,
                            ddp_p,
                            msg="Parameters differ between using ZeRO and "
                            "local optimizer",
                        )
                    iter += 1