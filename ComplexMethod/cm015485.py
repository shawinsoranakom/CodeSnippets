def test_init_2d_transformer_shard_diff_dim(self):
        model, ref_model = self._init_models()

        dp_size, tp_size = self.world_size // 2, 2
        global_mesh = init_device_mesh(
            device_type.type, (dp_size, tp_size), mesh_dim_names=("dp", "tp")
        )
        model = Transformer.parallelize(model, global_mesh["tp"], use_seq_parallel=True)

        def shard_placement_fn(param: nn.Parameter) -> Shard | None:
            if isinstance(param, DTensor):
                for placement in param.placements:
                    if isinstance(placement, Shard):
                        shard_dim = param.ndim - 1 - placement.dim
                        if not (shard_dim >= 0):
                            raise AssertionError(
                                f"Expected shard_dim >= 0, but got {shard_dim} for shape {param.shape}"
                            )
                        return Shard(shard_dim)
            return Shard(0)

        for layer in model.layers:
            fully_shard(
                layer, mesh=global_mesh["dp"], shard_placement_fn=shard_placement_fn
            )
        fully_shard(
            model, mesh=global_mesh["dp"], shard_placement_fn=shard_placement_fn
        )

        linear_weight_names = ["wq", "wk", "wv", "wo", "w1", "w2"]
        for param_name, param in model.named_parameters():
            if (
                any(n in param_name for n in linear_weight_names)
                and "weight" in param_name
            ):
                total_placement_dims = 0
                for placement in param.placements:
                    self.assertTrue(isinstance(placement, Shard))
                    total_placement_dims += placement.dim
                self.assertEqual(param.ndim, 2)
                # Check that FSDP shards on either dim-0 or dim-1, and TP
                # shards on the other
                self.assertEqual(total_placement_dims, 1)
            else:
                self.assertTrue(
                    any(isinstance(placement, Shard) for placement in param.placements)
                )

        for param, ref_param in zip(model.parameters(), ref_model.parameters()):
            full_param = param.full_tensor()
            self.assertEqual(full_param, ref_param)