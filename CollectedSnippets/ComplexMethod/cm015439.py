def _test_gradient_accumulation(
        self,
        mesh: DeviceMesh,
        reshard_after_forward: bool | int,
        mode: str,
        reshard_after_backward: bool,
        offload_policy: OffloadPolicy,
        reduce_scatter_only: bool,  # for HSDP
    ):
        if (
            (
                not reshard_after_backward
                and (reshard_after_forward is not False or mode == "some_mlps")
            )
            or (
                isinstance(offload_policy, CPUOffloadPolicy)
                and reshard_after_forward is not True
            )
            or (
                mesh.ndim != 2
            )  # may eventually need to change once decision on device mesh is made
        ):
            return  # skip since not common or applicable

        torch.manual_seed(42)
        batch_size, lin_dim, num_mlps, num_microbatches = (2, 32, 3, 3)
        if mode == "some_mlps":
            num_mlps_to_disable_reduce_scatter = 2
        modules = [nn.Linear(lin_dim, lin_dim)]
        modules.extend(MLP(lin_dim) for _ in range(num_mlps))
        model = nn.Sequential(*modules)
        ref_model = copy.deepcopy(model).to(device_type)
        replicate_fn = functools.partial(
            replicate,
            mesh=mesh,
            offload_policy=offload_policy,
        )
        for mlp in model[1:]:
            replicate_fn(mlp)
        replicate_fn(model)  # root gets the 1st linear
        ref_optim = torch.optim.Adam(ref_model.parameters(), lr=1e-2)
        optim = torch.optim.Adam(model.parameters(), lr=1e-2)

        def set_grad_sync_flag(
            module: nn.Module, is_last_microbatch: bool, recurse: bool = True
        ):
            if reduce_scatter_only:
                module.set_requires_all_reduce(is_last_microbatch, recurse=recurse)
            else:
                module.set_requires_gradient_sync(is_last_microbatch, recurse=recurse)

        def set_backward_flags(_model: nn.Module, is_last_microbatch: bool):
            if mode == "all":
                set_grad_sync_flag(_model, is_last_microbatch)
                if not reshard_after_backward:
                    _model.set_reshard_after_backward(is_last_microbatch)
            elif mode == "some_mlps":
                for mlp in model[1 : 1 + num_mlps_to_disable_reduce_scatter]:
                    set_grad_sync_flag(mlp, is_last_microbatch)
                    if not reshard_after_backward:
                        mlp.set_reshard_after_backward(is_last_microbatch)
            elif mode == "root_only":
                set_grad_sync_flag(model, is_last_microbatch, recurse=False)
                if not reshard_after_backward:
                    model.set_reshard_after_backward(is_last_microbatch, recurse=False)

        torch.manual_seed(42 + self.rank + 1)
        for iter_idx in range(5):
            comm_count_list = []

            for microbatch_idx in range(num_microbatches):
                is_last_microbatch = microbatch_idx == num_microbatches - 1
                set_backward_flags(model, is_last_microbatch)
                inp = torch.randn(batch_size, lin_dim, device=device_type.type)
                losses: list[torch.Tensor] = []
                for _model in (ref_model, model):
                    with CommDebugMode() as comm_mode:
                        losses.append(_model(inp).sum())
                        losses[-1].backward()
                    comm_count_list.append(comm_mode.get_comm_counts())
                self.assertEqual(losses[0], losses[1])

            comm_counts = defaultdict(int)
            for comm_count_dict in comm_count_list:
                for collective, count in comm_count_dict.items():
                    comm_counts[collective] += count

            all_gather_count = comm_counts[c10d_ops._allgather_base_]
            # reduce_scatter_count = comm_counts[c10d_ops._reduce_scatter_base_]
            all_reduce_count = comm_counts[c10d_ops.allreduce_]

            # Expect one reduce-scatter per MLP plus one for the root's linear
            # on the last microbatch
            # expected_reduce_scatter_count = 0
            expected_all_reduce_count = num_mlps + 1

            if mode == "some_mlps":
                # Expect additional reduce-scatters for non-disabled MLPs and
                # the root's linear
                expected_all_reduce_count += (
                    num_mlps - num_mlps_to_disable_reduce_scatter + 1
                ) * (num_microbatches - 1)
            elif mode == "root_only":
                # Expect additional reduce-scatters for all MLPs
                expected_all_reduce_count += (num_mlps) * (num_microbatches - 1)

            # self.assertEqual(reduce_scatter_count, expected_reduce_scatter_count)
            self.assertEqual(all_reduce_count, expected_all_reduce_count)

            # Expect one all-gather per MLP plus one for the root's linear in
            # the first microbatch's forward
            expected_all_gather_count = 0

            self.assertEqual(all_gather_count, expected_all_gather_count)

            for param in ref_model.parameters():
                if param.grad is not None:
                    dist.all_reduce(param.grad, op=dist.ReduceOp.AVG)
            check_sharded_parity(self, ref_model, model)
            for _optim in (optim, ref_optim):
                _optim.step()
                # When `set_to_none=False`, we are exercising mixing
                # gradient accumulation with and without communication
                _optim.zero_grad(set_to_none=(iter_idx % 2))