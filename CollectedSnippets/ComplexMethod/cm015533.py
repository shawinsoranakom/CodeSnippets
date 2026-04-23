def _test_custom_policy(self, use_uniform_kwargs: bool):
        print(f"use_uniform_kwargs={use_uniform_kwargs}")
        model = TransformerWithSharedParams.init(
            self.process_group,
            FSDPInitMode.NO_FSDP,
            DEVICEInitMode.DEVICE_BEFORE,
            {},
        )

        if use_uniform_kwargs:

            def lambda_fn(module: nn.Module):
                if module is model.bn:
                    return True
                elif isinstance(
                    module, (TransformerEncoderLayer, TransformerDecoderLayer)
                ):
                    return True
                return False

        else:

            def lambda_fn(module: nn.Module):
                if module is model.bn:
                    return {"sharding_strategy": ShardingStrategy.NO_SHARD}
                elif isinstance(module, TransformerEncoderLayer):
                    return True
                elif isinstance(module, TransformerDecoderLayer):
                    return {
                        "sharding_strategy": ShardingStrategy.SHARD_GRAD_OP,
                        "backward_prefetch": BackwardPrefetch.BACKWARD_POST,
                    }
                return False

        policy = CustomPolicy(lambda_fn)
        # Use a size-2 dummy PG to avoid clamping the sharding strategy to
        # `NO_SHARD` as for a size-1 PG
        process_group = DummyProcessGroup(rank=0, size=2)
        fp16_mp = MixedPrecision(param_dtype=torch.float16)
        fp32_mp = MixedPrecision()
        model = FSDP(
            model,
            process_group=process_group,
            auto_wrap_policy=policy,
            mixed_precision=fp16_mp,
        )
        encoder_layers = set(model.module.transformer.encoder.layers)
        decoder_layers = set(model.module.transformer.decoder.layers)
        bn = model.module.bn
        bn_strategy = (
            ShardingStrategy.FULL_SHARD
            if use_uniform_kwargs
            else ShardingStrategy.NO_SHARD
        )
        bn_prefetch = BackwardPrefetch.BACKWARD_PRE
        encoder_strategy = root_strategy = ShardingStrategy.FULL_SHARD
        encoder_prefetch = root_prefetch = BackwardPrefetch.BACKWARD_PRE
        decoder_strategy = (
            ShardingStrategy.FULL_SHARD
            if use_uniform_kwargs
            else ShardingStrategy.SHARD_GRAD_OP
        )
        decoder_prefetch = (
            BackwardPrefetch.BACKWARD_PRE
            if use_uniform_kwargs
            else BackwardPrefetch.BACKWARD_POST
        )
        for module in model.modules():
            if module is bn:
                self.assertTrue(isinstance(module, FSDP))
                self.assertEqual(module.sharding_strategy, bn_strategy)
                self.assertEqual(module.backward_prefetch, bn_prefetch)
                # We currently override batch norm modules to use fp32
                self.assertEqual(module.mixed_precision, fp32_mp)
            elif module in encoder_layers:
                self.assertTrue(isinstance(module, FSDP))
                self.assertEqual(module.sharding_strategy, encoder_strategy)
                self.assertEqual(module.backward_prefetch, encoder_prefetch)
                self.assertEqual(module.mixed_precision, fp16_mp)
            elif module in decoder_layers:
                self.assertTrue(isinstance(module, FSDP))
                self.assertEqual(module.sharding_strategy, decoder_strategy)
                self.assertEqual(module.backward_prefetch, decoder_prefetch)
                self.assertEqual(module.mixed_precision, fp16_mp)
            elif module is model:
                self.assertTrue(isinstance(module, FSDP))
                self.assertEqual(module.sharding_strategy, root_strategy)
                self.assertEqual(module.backward_prefetch, root_prefetch)
                self.assertEqual(module.mixed_precision, fp16_mp)
            else:
                self.assertFalse(isinstance(module, FSDP))