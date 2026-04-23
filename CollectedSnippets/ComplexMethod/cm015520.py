def _test_unshard_params_param_data(
        self,
        rank0_only: bool,
        offload_to_cpu: bool,
        cpu_offload: CPUOffload,
        mixed_precision: MixedPrecision | None,
        use_orig_params: bool,
    ):
        local_model = NestedWrappedModule.init(
            self.process_group,
            FSDPInitMode.NO_FSDP,
            DEVICEInitMode.DEVICE_BEFORE,
            fsdp_kwargs={"device_id": device_type.type},
            deterministic=True,
        )
        # Apply FSDP such that the root module does not have FSDP applied,
        # while there are multiple FSDP root submodules (as proven later)
        fsdp_model = NestedWrappedModule.init(
            self.process_group,
            FSDPInitMode.RECURSIVE,
            DEVICEInitMode.DEVICE_BEFORE,
            fsdp_kwargs={
                "cpu_offload": cpu_offload,
                "mixed_precision": mixed_precision,
                "use_orig_params": use_orig_params,
            },
            deterministic=True,
        )
        self.assertFalse(isinstance(fsdp_model, FSDP))
        # Hard code the following names because getting them is non-trivial
        non_fsdp_managed_param_names = {
            "module.0.weight",
            "module.0.bias",
            "module.3.weight",
            "module.3.bias",
        }

        with FSDP.summon_full_params(
            fsdp_model,
            rank0_only=rank0_only,
            writeback=not rank0_only,
            offload_to_cpu=offload_to_cpu,
        ):
            if not rank0_only or self.rank == 0:
                for p1, (n2, p2) in zip(
                    local_model.parameters(), fsdp_model.named_parameters()
                ):
                    self.assertEqual(p1.shape, p2.shape)
                    if (
                        offload_to_cpu
                        and clean_tensor_name(n2) not in non_fsdp_managed_param_names
                    ):
                        self.assertEqual(torch.device("cpu"), p2.device)
                    else:
                        self.assertEqual(p1.device, p2.device)
                    self.assertEqual(
                        p1.dtype, p2.dtype
                    )  # even if FSDP uses mixed precision
                    self.assertEqual(p1, p2)
                    self.assertTrue(isinstance(p2, nn.Parameter))
            else:
                # Check that each `FlatParameter` has the sharded size as a
                # proxy for it being resharded
                for handle in traversal_utils._get_fsdp_handles(fsdp_model):
                    if handle.uses_sharded_strategy:
                        self.assertEqual(
                            handle.flat_param.shape, handle.flat_param._sharded_size
                        )
                    else:
                        self.assertEqual(
                            handle.flat_param.shape,
                            handle.flat_param._unpadded_unsharded_size,
                        )

        # Prove the number of FSDP roots after lazy initialization
        num_fsdp_roots = 0
        for fsdp_state in traversal_utils._get_fsdp_states(fsdp_model):
            num_fsdp_roots += fsdp_state._is_root
        self.assertGreater(num_fsdp_roots, 1)