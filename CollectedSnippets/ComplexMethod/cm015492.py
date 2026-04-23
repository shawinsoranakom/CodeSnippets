def test_communication(
        self,
        device,
        nested_model: bool,
        use_no_sync: bool,
        sharding_strategy: ShardingStrategy | None,
    ):
        """
        Tests FSDP's communication cost in terms of calls to collective
        communication primitives (i.e. all-gather and reduce-scatter).
        Arguments:
            nested_model (bool): If ``True``, uses ``NestedWrappedModule``,
                which has nested FSDP instances; if ``False``, uses the default
                model, which does not have nested FSDP instances.
            use_no_sync (bool): If ``True``, runs some iterations inside the
                ``no_sync()`` context manager to accumulate gradients, followed
                by some iterations outside the context manager; if ``False``,
                only runs some iterations outside the context manager.
            sharding_strategy (Optional[ShardingStrategy]): Configures the
                FSDP algorithm.
        """
        # Enable execution order checking
        dist.set_debug_level(dist.DebugLevel.DETAIL)
        # Initialize the model and inputs
        fsdp_model = self._init_model(device_type, nested_model, sharding_strategy)
        batch = fsdp_model.module.get_input(device_type)
        # Count the number of FSDP instances that manage parameters since the
        # number of collectives are a function of this number
        num_fsdp = sum(
            (isinstance(m, FSDP) and len(m.params) > 0) for m in fsdp_model.modules()
        )
        # If `use_no_sync=True`, we run `num_iters` iterations inside
        # `no_sync()` followed by `num_iters` iterations outside `no_sync()`,
        # and if `use_no_sync=False`, we only run `num_iters` iterations
        # outside `no_sync()`
        num_iters = 3
        with (
            patch("torch.distributed.all_gather_into_tensor") as mock_all_gather,
            patch("torch.distributed.reduce_scatter_tensor") as mock_reduce_scatter,
        ):

            def reset_mocks():
                mock_all_gather.reset_mock()
                mock_reduce_scatter.reset_mock()

            # Check the communication cost when using `no_sync()`
            if use_no_sync:
                for i in range(num_iters):
                    reset_mocks()
                    self._run_iter(fsdp_model, batch, use_no_sync=True)
                    num_all_gathers = mock_all_gather.call_count
                    num_reduce_scatters = mock_reduce_scatter.call_count
                    ref_num_all_gathers = self._get_ref_num_all_gathers(
                        num_fsdp,
                        sharding_strategy,
                        is_first_iter=i == 0,
                        is_last_iter_no_sync=i > 0,
                    )
                    ref_num_reduce_scatters = self._get_ref_num_reduce_scatters(
                        num_fsdp,
                        in_no_sync=True,
                    )
                    self.assertEqual(num_all_gathers, ref_num_all_gathers)
                    self.assertEqual(num_reduce_scatters, ref_num_reduce_scatters)
            # Check the normal communication cost (when not using `no_sync()`)
            for i in range(num_iters):
                reset_mocks()
                self._run_iter(fsdp_model, batch, use_no_sync=False)
                num_all_gathers = mock_all_gather.call_count
                num_reduce_scatters = mock_reduce_scatter.call_count
                ref_num_all_gathers = self._get_ref_num_all_gathers(
                    num_fsdp,
                    sharding_strategy,
                    is_first_iter=not use_no_sync and i == 0,
                    is_last_iter_no_sync=use_no_sync and i == 0,
                )
                ref_num_reduce_scatters = self._get_ref_num_reduce_scatters(
                    num_fsdp,
                    in_no_sync=False,
                )
                self.assertEqual(num_all_gathers, ref_num_all_gathers)
                self.assertEqual(num_reduce_scatters, ref_num_reduce_scatters)