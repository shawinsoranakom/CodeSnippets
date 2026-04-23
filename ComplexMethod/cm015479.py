def test_shard_dtensor_parameters(self):
        dp_size = 2 if self.world_size > 2 else 1
        global_mesh = init_device_mesh(
            device_type.type,
            (dp_size, self.world_size // dp_size),
            mesh_dim_names=("dp", "tp"),
        )
        dp_mesh, tp_mesh = global_mesh["dp"], global_mesh["tp"]
        # Use odd dim sizes to test uneven shards
        model = MLP(9, dim_multiplier=3)
        orig_params = [param.detach().clone() for param in model.parameters()]
        orig_param_names = [param_name for param_name, _ in model.named_parameters()]
        parallelize_module(
            model,
            tp_mesh,
            {"in_proj": ColwiseParallel(), "out_proj": RowwiseParallel()},
        )
        fully_shard(model, mesh=dp_mesh)
        sharded_params = list(model.parameters())
        self.assertEqual(len(orig_params), len(sharded_params))
        for orig_param_name, orig_param, sharded_param in zip(
            orig_param_names, orig_params, sharded_params
        ):
            self.assertIsInstance(sharded_param, DTensor)
            self.assertEqual(sharded_param.device_mesh, global_mesh)
            self.assertEqual(sharded_param.size(), orig_param.size())
            self.assertEqual(sharded_param.stride(), orig_param.stride())
            if "in_proj" in orig_param_name:
                expected_placements = (
                    _StridedShard(0, split_factor=tp_mesh.size()),
                    Shard(0),
                )
            elif "out_proj" in orig_param_name and "weight" in orig_param_name:
                expected_placements = (Shard(0), Shard(1))
            else:
                expected_placements = (Shard(0), Replicate())
            self.assertEqual(sharded_param._spec.placements, expected_placements)