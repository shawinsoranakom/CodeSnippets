def test_1d_process_group_init(self):
        if not (self.world_size == 4):
            raise AssertionError(f"Expected world_size == 4, but got {self.world_size}")
        # For convenience, use device mesh's infra to construct the DP PG
        # (in practice, the trainer would do it manually via `new_group()`)
        dp_size = 2
        global_mesh = init_device_mesh(
            device_type.type,
            (dp_size, self.world_size // dp_size),
            mesh_dim_names=("dp", "tp"),
        )
        ref_dp_mesh, tp_mesh = global_mesh["dp"], global_mesh["tp"]
        dp_pg = ref_dp_mesh.get_group(0)

        # Check the `from_group()` API for correctness
        dp_mesh = DeviceMesh.from_group(dp_pg, device_type.type, mesh_dim_names=("dp",))
        # Only compare the mesh tensors, not `DeviceMesh` objects themselves,
        # since the ref has a parent mesh, while the `from_group` one does not
        self.assertEqual(dp_mesh.mesh, ref_dp_mesh.mesh)
        self.assertEqual(dp_mesh._coordinate_on_dim, ref_dp_mesh._coordinate_on_dim)
        self.assertEqual(dp_mesh._dim_group_names, ref_dp_mesh._dim_group_names)

        # Check 1D FSDP forward/backward parity over the DP mesh
        # NOTE: We cannot use 2D DTensor-based training here because the DP
        # mesh from `from_group` does not respect the parent mesh.
        torch.manual_seed(42)
        mlp_dim = 8
        ref_model = MLP(mlp_dim)
        for param in ref_model.parameters():
            dist.broadcast(param.detach(), src=0)
        model = copy.deepcopy(ref_model)

        # Parallelize the test model with the ref DP mesh
        for module in (ref_model.in_proj, ref_model.out_proj, ref_model):
            fully_shard(module, mesh=ref_dp_mesh)
        # Parallelize the test model with the new DP mesh from the PG
        for module in (model.in_proj, model.out_proj, model):
            fully_shard(module, mesh=dp_mesh)

        # Ensure that TP ranks have the same input
        inp = torch.randn((4, mlp_dim), device=device_type.type)
        if self.rank in (0, 1):
            dist.broadcast(inp, src=0, group=tp_mesh.get_group(0))
        elif self.rank in (2, 3):
            dist.broadcast(inp, src=2, group=tp_mesh.get_group(0))

        ref_loss = ref_model(inp).sum()
        ref_loss.backward()
        loss = model(inp).sum()
        loss.backward()
        self.assertEqual(loss, ref_loss)
        for param, ref_param in zip(model.parameters(), ref_model.parameters()):
            # Cannot compare `DTensor`s directly since their meshes are not
            # equal due to the ref parameter's mesh having a parent mesh while
            # the other's mesh does not
            self.assertEqual(param.to_local(), ref_param.to_local())
            self.assertEqual(param.device_mesh.mesh, ref_param.device_mesh.mesh)
            self.assertEqual(param.grad.to_local(), ref_param.grad.to_local())
            self.assertEqual(
                param.grad.device_mesh.mesh, ref_param.grad.device_mesh.mesh
            )