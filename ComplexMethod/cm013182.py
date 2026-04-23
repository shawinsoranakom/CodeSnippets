def _test_fsdp_parity(
        self,
        model_class: type[FSDPTestModel],
        fsdp_init_mode: FSDPInitMode,
        device_init_mode: DEVICEInitMode,
        ref_init_fn: Callable | None = None,
        num_iters: int = 2,
        save_model: bool = True,
        cpu_offload: CPUOffload = CPUOffload(),
        backward_prefetch: BackwardPrefetch | None = None,
        sharding_strategy: ShardingStrategy | None = None,
        mixed_precision: MixedPrecision | None = None,
        forward_prefetch: bool = False,
        use_orig_params: bool = False,
        enable_sharded_grad_scaler: bool = False,
        use_pure_fp16: bool = False,
        init_kwargs: dict[str, Any] | None = None,
        sharded_grad_scaler_kwargs: dict[str, Any] | None = None,
        **fsdp_kwargs,
    ):
        """
        Tests FSDP training against a reference, which defaults to DDP but
        may be customized with ``ref_init_fn``.

        Args:
            model_class (Type[FSDPTestModel]): A model class that inherits from
                ``FSDPTestModel``, which defines the expected interface.
            fsdp_init_mode (FSDPInitMode): The mode to initialize the
                FSDP-wrapped model. This should not be ``NO_FSDP``.
            ref_init_fn (Optional[Callable]): A callable to invoke that wraps a
                non-wrapped model to construct the reference model, where this
                wrapper should provide data parallel semantics. If ``None``,
                then the callable defaults to the DDP constructor.
        """
        if fsdp_init_mode == FSDPInitMode.NO_FSDP:
            raise AssertionError("Expects an FSDP init mode that wraps with FSDP")
        if init_kwargs is None:
            init_kwargs = {}
        lr = 1e-2
        rank = self.process_group.rank()
        # Establish reference behavior with DDP
        model = model_class.init(
            self.process_group,
            FSDPInitMode.NO_FSDP,
            DEVICEInitMode.DEVICE_BEFORE,
            deterministic=True,
            **init_kwargs,
        )
        if ref_init_fn is None:
            if TEST_HPU:
                ref_model = DDP(
                    model, device_ids=[DEVICE_TYPE], output_device=DEVICE_TYPE
                )
            elif DEVICE_TYPE == "cpu":
                ref_model = DDP(model)
            else:
                ref_model = DDP(model, device_ids=[rank], output_device=rank)
        else:
            ref_model = ref_init_fn(model)
        if use_pure_fp16:
            ref_model = ref_model.half()
        ref_loss = self._train_for_several_steps(
            ref_model,
            num_iters,
            autocast=mixed_precision is not None,
            lr=lr,
            fsdp_cpu_offload=cpu_offload,
            mixed_precision=mixed_precision,
            enable_sharded_grad_scaler=enable_sharded_grad_scaler,
            use_pure_fp16=use_pure_fp16,
            sharded_grad_scaler_kwargs=sharded_grad_scaler_kwargs,
        )
        ddp_params = list(ref_model.parameters())
        # Check against FSDP behavior
        fsdp_kwargs.update(
            {
                "cpu_offload": cpu_offload,
                "backward_prefetch": backward_prefetch,
                "sharding_strategy": sharding_strategy,
                "mixed_precision": mixed_precision,
                "forward_prefetch": forward_prefetch,
                "use_orig_params": use_orig_params,
            }
        )
        try:
            fsdp_model = model_class.init(
                self.process_group,
                fsdp_init_mode,
                device_init_mode,
                fsdp_kwargs,
                deterministic=True,
                **init_kwargs,
            )
        except Exception as e:
            raise ValueError(f"Initializing {model_class} raised error {str(e)}") from e
        if not isinstance(fsdp_model, FSDP):
            # Enforce that we wrap with top-level FSDP since we are comparing
            # assuming a data parallel reference and some test models may not
            # do so in their `init()` method
            fsdp_model = FSDP(fsdp_model, self.process_group, **fsdp_kwargs)
        if use_pure_fp16:
            # Change the model parameter dtype after FSDP initialization
            fsdp_model = fsdp_model.half()
        if device_init_mode == DEVICEInitMode.DEVICE_AFTER:
            fsdp_model = fsdp_model.to(DEVICE_TYPE)
        offload_params = cpu_offload is not None and cpu_offload.offload_params
        # Offloading parameters with `DEVICE_AFTER` should raise an error during
        # lazy initialization due to the parameter devices not being CPU;
        # otherwise, all parameter devices should be CPU
        expects_device_error = (
            offload_params and device_init_mode == DEVICEInitMode.DEVICE_AFTER
        )
        expects_cpu_device = (
            offload_params and device_init_mode != DEVICEInitMode.DEVICE_AFTER
        )
        if expects_cpu_device:
            cpu_device = torch.device("cpu")
            for param in fsdp_model.parameters():
                self.assertEqual(param.device, cpu_device)
        context = (
            self.assertRaisesRegex(
                RuntimeError,
                "An FSDP-managed module with parameter CPU offloading enabled "
                f"has parameters on {DEVICE_TYPE}",
            )
            if expects_device_error
            else nullcontext()
        )
        with context:
            fsdp_loss = self._train_for_several_steps(
                fsdp_model,
                num_iters,
                autocast=False,
                lr=lr,
                fsdp_cpu_offload=cpu_offload,
                save_model=save_model,
                mixed_precision=mixed_precision,
                enable_sharded_grad_scaler=enable_sharded_grad_scaler,
                use_pure_fp16=use_pure_fp16,
                sharded_grad_scaler_kwargs=sharded_grad_scaler_kwargs,
            )
        # No need to check for parameter and loss parity if expecting an error
        if expects_device_error:
            return
        # Check parameter devices are CPU if offloading to CPU before calling
        # `get_full_params()`, which will cast the parameters to FP32
        if offload_params:
            cpu_device = torch.device("cpu")
            for param in fsdp_model.parameters():
                self.assertEqual(param.device, cpu_device)
            fsdp_loss = fsdp_loss.to(DEVICE_TYPE)
        fsdp_unsharded_params = get_full_params(fsdp_model)
        # Do not check dtype since the reference DDP loss may not be the same
        # dtype as the FSDP loss in the case of mixed precision
        torch.testing.assert_close(ref_loss, fsdp_loss, check_dtype=False)
        # Do not check for parameter parity if using mixed precision since (1)
        # the DDP parameters are in FP16 (from `half()`) while the FSDP
        # parameters are in FP32 (from `summon_full_params()`) and (2) DDP runs
        # the optimizer in FP16 while FSDP runs it in FP32
        # TODO: Disable checking the parameters for pure FP16 due to floating
        # point inaccuracy. Note that this means that the backward pass is not
        # checked: https://github.com/pytorch/pytorch/issues/90784
        if mixed_precision is None and not use_pure_fp16:
            self.assertEqual(
                ddp_params,
                fsdp_unsharded_params,
                exact_device=True,
                msg="FSDP did not match DDP",
            )