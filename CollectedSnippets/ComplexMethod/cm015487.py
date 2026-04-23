def forward(self, tup):
        inp, cls, fsdp, mp_config, full_precision_param_dtype = tup
        if self.run_checks:
            # Param and input should be the mixed precision type
            expected_param_type = (
                mp_config.param_dtype
                if mp_config.param_dtype is not None
                else self._orig_param_type
            )
            expected_buffer_type = (
                mp_config.buffer_dtype
                if mp_config.buffer_dtype is not None
                else self._orig_buffer_dtype
            )
            cls.assertEqual(inp.dtype, expected_param_type)
            # Buffer should be in specified precision as well.
            cls.assertEqual(getattr(self, self.buffer_name).dtype, expected_buffer_type)

            # In FSDP, self.params should point to the right type.
            num_active_fsdp = 0
            for fsdp_module in FSDP.fsdp_modules(fsdp):
                fsdp_managed_params = fsdp_module.params
                # Single param assumption
                cls.assertEqual(1, len(fsdp_managed_params))
                for param in fsdp_managed_params:
                    # FSDP unit is currently active if it is not using the param
                    # local shard. This supports both FULL_SHARD and SHARD_GRAD_OP
                    # cases. In FULL_SHARD, we have the additional property that
                    # param._full_param_padded has not been freed.
                    param_is_sharded = (
                        fsdp_module.sharding_strategy != ShardingStrategy.NO_SHARD
                        and fsdp_module.world_size > 1
                    )
                    is_fsdp_unit_active = (
                        param_is_sharded
                        and param.data.data_ptr() != param._local_shard.data_ptr()
                    )
                    if is_fsdp_unit_active:
                        num_active_fsdp += 1
                        # This FSDP unit is active, verify param points to mixed
                        cls.assertEqual(param.dtype, expected_param_type)
                        # _unshard should have also freed the fp16 shard.
                        # Shard is never allocated if param_dtype mixed precision is not
                        # enabled.
                        if mp_config.param_dtype is not None:
                            cls.assertEqual(0, param._mp_shard.untyped_storage().size())
                        else:
                            cls.assertFalse(hasattr(param, "_mp_shard"))
                    elif param_is_sharded:
                        # This FSDP unit is not active as full param has been
                        # freed or not yet allocated. Ensure param points to full
                        # precision param.
                        cls.assertEqual(param.dtype, full_precision_param_dtype)
            # We should have gotten at least one active FSDP unit for sharded
            # (world size > 1) cases. For cases where param is not sharded
            # (ie world_size == 1) it is a bit hard to check if FSDP unit is active
            # as we'd always point to the local shard, so we rely on the forward
            # pass self.lin(inp) working well and inp being reduced precision to
            # implicitly validate that the param is indeed in the reduced precision.
            if cls.world_size > 1:
                cls.assertGreater(num_active_fsdp, 0)

        return (self.lin(inp), cls, fsdp, mp_config, full_precision_param_dtype)