def test_ddp_uneven_inputs(self):
            dim = 1000
            batch = 1
            # Create a variety of models to run uneven input tests on.
            large_model = nn.Sequential(
                nn.Conv2d(1, 20, 5),
                nn.ReLU(),
                nn.Conv2d(20, 32, 5),
                nn.ReLU(),
                nn.Conv2d(32, 256, 5),
                nn.ReLU(),
            )
            small_model = nn.Linear(dim, dim, bias=False)
            bn_net = BatchNormNet()

            class UnusedParamModule(nn.Module):
                def __init__(self, unused_params_rank):
                    super().__init__()
                    self.t0 = Task()
                    self.t1 = Task()
                    self.unused_params_rank = unused_params_rank

                def task_parameters(self):
                    return (self.t0.p, self.t1.p)

                def forward(self, x, rank):
                    return (
                        self.t1(self.t0(x))
                        if rank != self.unused_params_rank
                        else self.t1(x)
                    )

            unjoined_rank_with_unused_params_model = UnusedParamModule(1)
            joined_rank_with_unused_params_model = UnusedParamModule(0)

            rank = self.rank
            models_to_test = [
                # Network with batchnorm
                DDPUnevenTestInput(
                    name="batch_norm_net",
                    model=bn_net,
                    inp=torch.ones(batch, 2, device=rank),
                    sync_interval=1,
                ),
                DDPUnevenTestInput(
                    name="large_conv_model",
                    model=large_model,
                    inp=torch.ones(batch, batch, dim, dim, device=rank),
                    sync_interval=1,
                ),
                DDPUnevenTestInput(
                    name="small_model",
                    model=small_model,
                    inp=torch.ones(batch, dim, device=rank),
                    sync_interval=1,
                ),
                # Unused parameter test where rank that does not join early has unused params
                DDPUnevenTestInput(
                    name="unjoined_rank_with_unused_params_model",
                    model=unjoined_rank_with_unused_params_model,
                    inp=(torch.ones(batch, 2, device=rank), rank),
                    sync_interval=1,
                ),
                # Unused parameter test where rank that does join early has unused params
                DDPUnevenTestInput(
                    name="joined_rank_with_unused_params_model",
                    model=joined_rank_with_unused_params_model,
                    inp=(torch.ones(batch, 2, device=rank), rank),
                    sync_interval=1,
                ),
            ]

            # Test models that have hook installed.
            models_with_hook = [
                DDPUnevenTestInput(
                    name="small_model_allreduce_hook",
                    model=small_model,
                    hook=default.allreduce_hook,
                    state=None,
                    inp=torch.ones(batch, dim, device=rank),
                    sync_interval=1,
                ),
                DDPUnevenTestInput(
                    name="small_model_power_sgd_hook",
                    model=small_model,
                    hook=powerSGD.powerSGD_hook,
                    state=powerSGD.PowerSGDState(
                        process_group=None,
                        matrix_approximation_rank=1,
                        # Config so that powerSGD runs immediately instead of
                        # allreduce.
                        start_powerSGD_iter=1,
                        warm_start=False,
                        use_error_feedback=False,
                    ),
                    inp=torch.ones(batch, dim, device=rank),
                    sync_interval=1,
                ),
            ]
            models_to_test.extend(models_with_hook)

            # Add resnet model if we have torchvision installed.
            if HAS_TORCHVISION:
                resnet_model = torchvision.models.resnet50()
                models_to_test.append(
                    DDPUnevenTestInput(
                        name="resnet_model",
                        model=resnet_model,
                        inp=torch.ones(1, 3, 1000, 1000),
                        sync_interval=1,
                    )
                )

            # Test with no_sync every 2, 3, 4, ... iterations.
            models_with_sync = []
            for i, test_input in enumerate(models_to_test):
                models_with_sync.append(
                    DDPUnevenTestInput(
                        name=test_input.name,
                        model=test_input.model,
                        inp=test_input.inp,
                        sync_interval=i + 2,
                    )
                )

            throw_on_early_term_tests = []
            for test_input in models_to_test:
                throw_on_early_term_tests.append(
                    DDPUnevenTestInput(
                        name=test_input.name,
                        model=test_input.model,
                        inp=test_input.inp,
                        sync_interval=test_input.sync_interval,
                        throw_on_early_termination=True,
                    )
                )

            models_to_test.extend(models_with_sync)
            models_to_test.extend(throw_on_early_term_tests)

            # 0 iteration tests for when one process does not train model at all, so
            # we must shadow the broadcast calls made when rebuilding buckets.
            baseline_num_iters = [0, 5]
            iteration_offsets = [2, 3, 10]
            num_uneven_ranks = [1]
            if dist.get_world_size() > 2:
                num_uneven_ranks.append(2)
            iteration_mappings = []
            # Generate rank : num_iters mappings for various uneven input scenarios.
            # This includes cases where rank 0 joins early and all other ranks join
            # later, and scenarios where multiple ranks join early, but at different
            # iterations, and later ranks join later.
            for num_early_join_ranks in num_uneven_ranks:
                for baseline_iter in baseline_num_iters:
                    for offset in iteration_offsets:
                        mapping = dict.fromkeys(
                            range(num_early_join_ranks), baseline_iter
                        )
                        # if num_early_join_ranks > 1, ranks > 0 that will join early
                        # iterate offset//2 more times than rank 0, to test nodes
                        # depleting inputs at different times.
                        if num_early_join_ranks > 1:
                            for rank in mapping:
                                if rank > 0:
                                    mapping[rank] += offset // 2
                        mapping.update(
                            dict.fromkeys(
                                range(num_early_join_ranks, dist.get_world_size()),
                                baseline_iter + offset,
                            )
                        )
                        iteration_mappings.append(mapping)

            for test_case, iteration_mapping in itertools.product(
                models_to_test, iteration_mappings
            ):
                if self.rank == 0:
                    print(
                        f"""Running test: {test_case.name} sync interval
                        {test_case.sync_interval} with iteration mapping
                        {iteration_mapping}"""
                    )
                self._run_uneven_inputs_test(
                    test_case,
                    iteration_mapping,
                    find_unused_params=("unused_params_model" in test_case.name),
                )