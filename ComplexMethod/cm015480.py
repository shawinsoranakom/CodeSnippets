def test_meta_device_1d_init(self):
        default_pg = torch.distributed.distributed_c10d._get_default_group()
        mesh = init_device_mesh(device_type.type, mesh_shape=(default_pg.size(),))
        # Test both even sharding (8), uneven sharding (3), and empty local tensor (1)
        for mlp_dim in (8, 3, 1):
            # cover foreach_copy code path for bf16
            for mp_policy in (
                MixedPrecisionPolicy(),
                MixedPrecisionPolicy(
                    param_dtype=torch.bfloat16, reduce_dtype=torch.float32
                ),
            ):
                with torch.device("meta"):
                    model = nn.Sequential(
                        MLP(mlp_dim, dim_multiplier=1, with_buffer=True, bias=False),
                        MLP(mlp_dim, dim_multiplier=1, bias=False),
                    )
                    for param in model.parameters():
                        self.assertEqual(param.device, torch.device("meta"))
                    fully_shard(model[0], mesh=mesh, mp_policy=mp_policy)
                    fully_shard(model[1], mesh=mesh, mp_policy=mp_policy)
                    fully_shard(model, mesh=mesh, mp_policy=mp_policy)
                for param in model.parameters():
                    self.assertEqual(param.device, torch.device("meta"))
                self._test_to_empty_and_reset_parameters(model, mesh, mlp_dim)

        # Test that we can call `fully_shard` under meta-device context and
        # that `init_device_mesh` call still works
        mlp_dim = 8
        with torch.device("meta"):
            model = nn.Sequential(MLP(mlp_dim, with_buffer=True), MLP(mlp_dim))
            for param in model.parameters():
                self.assertEqual(param.device, torch.device("meta"))
            for module in (model[0], model[1], model):
                fully_shard(module)
        for param in model.parameters():
            self.assertEqual(param.device, torch.device("meta"))
        self._test_to_empty_and_reset_parameters(model, mesh, mlp_dim)