def _run_test_mixed_precision_e2e(
        self,
        mp_config,
        cpu_offload,
        backward_prefetch,
        forward_prefetch,
        full_precision_param_dtype,
        sharding_strategy,
        enable_sharded_grad_scaler,
    ):
        torch.cuda.set_device(self.rank)
        fsdp_models = [
            self._get_simple_model(
                param_dtype=full_precision_param_dtype,
                sharding_strategy=sharding_strategy,
                cpu_offload=cpu_offload,
                mixed_precision=mp_config,
                backward_prefetch=backward_prefetch,
                forward_prefetch=forward_prefetch,
            ),
            self._get_simple_nested_model(
                param_dtype=full_precision_param_dtype,
                run_checks=True,
                sharding_strategy=sharding_strategy,
                cpu_offload=cpu_offload,
                mixed_precision=mp_config,
                backward_prefetch=backward_prefetch,
                forward_prefetch=forward_prefetch,
            ),
        ]
        for model in fsdp_models:
            if not cpu_offload.offload_params:
                model.cuda()

            # Patch reduce_scatter to add validation for mixed precision types.
            orig_reduce_scatter = dist.reduce_scatter_tensor
            test_reduce_scatter = partial(
                self._reduce_scatter_validate_mp,
                orig_reduce_scatter,
                mp_config,
                True,
            )
            with patch_reduce_scatter(test_reduce_scatter, full_precision_param_dtype):
                scaler = ShardedGradScaler(enabled=enable_sharded_grad_scaler)
                optim = torch.optim.Adam(model.parameters())

                for _ in range(3):
                    inp = torch.randn(
                        3, 10, device="cuda", dtype=full_precision_param_dtype
                    )
                    # Forward pass of LinearMixedPrecision check casting of
                    # inputs, params, buffers.
                    act, *_ = model(
                        (inp, self, model, mp_config, full_precision_param_dtype)
                    )
                    # Buffers should be casted.
                    for buf in model.buffers():
                        if mp_config.buffer_dtype is not None:
                            self.assertEqual(buf.dtype, mp_config.buffer_dtype)
                        else:
                            self.assertEqual(buf.dtype, _BUFFER_ORIG_DTYPE)
                    # p._mp_shard should be freed.
                    if mp_config.param_dtype is not None:
                        self._validate_mp_shard_freed(model)
                    else:
                        # We never should have allocated an _mp_shard.
                        self._validate_no_mp_shard(model)

                    loss = act.sum()
                    loss = scaler.scale(loss)
                    if mp_config.param_dtype is not None:
                        self.assertEqual(loss.dtype, mp_config.param_dtype)
                    else:
                        self.assertEqual(loss.dtype, full_precision_param_dtype)
                    # Will run patched reduce scatter that validates mixed_precision
                    # types in backward.
                    loss.backward()
                    # Buffers stay casted even after backwards.
                    for buf in model.buffers():
                        if mp_config.buffer_dtype is not None:
                            self.assertEqual(buf.dtype, mp_config.buffer_dtype)
                        else:
                            self.assertEqual(buf.dtype, _BUFFER_ORIG_DTYPE)
                    # p._mp_shard should be freed.
                    if mp_config.param_dtype is not None:
                        self._validate_mp_shard_freed(model)
                    else:
                        self._validate_no_mp_shard(model)

                    # Ensure params and grads are in full precision,
                    # as after fwd/backward we maintain full precision shards.
                    for param in model.parameters():
                        self.assertEqual(param.dtype, full_precision_param_dtype)
                        if param.grad is not None:
                            self.assertEqual(
                                param.grad.dtype, full_precision_param_dtype
                            )

                    # Unscale the gradients and step
                    scaler.step(optim)
                    # Update the scale factor
                    scaler.update()

                    # Summon full params should be in full precision
                    with model.summon_full_params(model):
                        # It is not expected for summon_full_params to allocate
                        # a mixed precision shard.
                        if mp_config.param_dtype is not None:
                            self._validate_mp_shard_freed(model)
                        else:
                            self._validate_no_mp_shard(model)
                        params = list(model.parameters())
                        for p in params:
                            self.assertEqual(p.dtype, full_precision_param_dtype)

                        # Note that buffers are cast only once and only restored
                        # to the original buffer dtype in state_dict, so
                        # summon_full_params is not expected to restore buffer
                        # types to their original.
                        named_buffers = dict(model.named_buffers())
                        for v in named_buffers.values():
                            if mp_config.buffer_dtype is not None:
                                self.assertEqual(v.dtype, mp_config.buffer_dtype)
                            else:
                                self.assertEqual(v.dtype, _BUFFER_ORIG_DTYPE)

                    # state_dict should be in full precision
                    state_dict = {k: v.clone() for k, v in model.state_dict().items()}
                    for name, tensor in state_dict.items():
                        # Parameters and buffers are checkpointed in their
                        # original dtypes, which may be different.
                        if name in named_buffers:
                            self.assertEqual(tensor.dtype, _BUFFER_ORIG_DTYPE)
                        else:
                            self.assertEqual(
                                tensor.dtype,
                                full_precision_param_dtype,
                                f"{name}: {tensor.dtype} vs {full_precision_param_dtype}",
                            )

                    # After state_dict, buffer's dtype should have been restored
                    # to the mixed precision one.
                    for buf in model.buffers():
                        if mp_config.buffer_dtype is not None:
                            self.assertEqual(buf.dtype, mp_config.buffer_dtype)
                        else:
                            self.assertEqual(buf.dtype, _BUFFER_ORIG_DTYPE)