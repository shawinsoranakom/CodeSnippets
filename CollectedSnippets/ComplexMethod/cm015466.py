def test_dtensor_train_parity(self):
        """Train parity for FSDP/HSDP/DDP with DTensors on SPMD meshes."""
        ws = self.world_size
        world_mesh = init_device_mesh(
            device_type.type, (ws,), mesh_dim_names=("world",)
        )
        # (sizes, names, dp_dims, use_tp, reshard, dp_pg_source, use_rep_fsdp)
        cases = [
            # 1D: FSDP
            (
                (ws,),
                ("fsdp",),
                DataParallelMeshDims(shard="fsdp"),
                False,
                True,
                None,
                False,
            ),
            # 1D: FSDP with reshard_after_forward=False
            (
                (ws,),
                ("fsdp0",),
                DataParallelMeshDims(shard="fsdp0"),
                False,
                False,
                None,
                False,
            ),
            # 1D: DDP-only
            (
                (ws,),
                ("ddp",),
                DataParallelMeshDims(replicate="ddp"),
                False,
                True,
                None,
                False,
            ),
            # 1D: replicate_with_fsdp
            (
                (ws,),
                ("ddp0",),
                DataParallelMeshDims(replicate="ddp0"),
                False,
                True,
                None,
                True,
            ),
        ]
        if ws >= 4:
            cases.extend(
                [
                    # HSDP 2D
                    (
                        (2, ws // 2),
                        ("rep", "shard"),
                        DataParallelMeshDims(shard="shard", replicate="rep"),
                        False,
                        True,
                        "world",
                        False,
                    ),
                    # Multi-shard FSDP
                    (
                        (2, ws // 2),
                        ("dp0", "dp1"),
                        DataParallelMeshDims(shard=("dp0", "dp1")),
                        False,
                        True,
                        "world",
                        False,
                    ),
                    # FSDP+TP
                    (
                        (2, ws // 2),
                        ("fsdp1", "tp"),
                        DataParallelMeshDims(shard="fsdp1"),
                        True,
                        True,
                        "fsdp1",
                        False,
                    ),
                    # FSDP+TP with reshard_after_forward=False
                    (
                        (2, ws // 2),
                        ("fsdp2", "tp0"),
                        DataParallelMeshDims(shard="fsdp2"),
                        True,
                        False,
                        "fsdp2",
                        False,
                    ),
                    # HSDP+TP 3D
                    (
                        (1, ws // 2, 2),
                        ("rep0", "fsdp3", "tp1"),
                        DataParallelMeshDims(shard="fsdp3", replicate="rep0"),
                        True,
                        True,
                        "fsdp3",
                        False,
                    ),
                    # Multi-dim replicate
                    (
                        (1, ws // 2, 2),
                        ("ddp1", "ddp2", "fsdp4"),
                        DataParallelMeshDims(shard="fsdp4", replicate=("ddp1", "ddp2")),
                        False,
                        True,
                        "world",
                        False,
                    ),
                ]
            )
        mlp_dim = 16
        for sizes, names, dp_dims, use_tp, reshard, dp_pg_src, use_rep in cases:
            with self.subTest(
                names=names, use_tp=use_tp, reshard=reshard, use_rep=use_rep
            ):
                mesh = world_mesh._unflatten(0, sizes, names)

                torch.manual_seed(42)
                model = MLP(mlp_dim, device=device_type)
                ref_model = copy.deepcopy(model)

                partition_fn = _tp_partition_fn if use_tp else None
                distribute_module(model, mesh, partition_fn)

                if use_rep:
                    replicate_with_fsdp(model, mesh=mesh, dp_mesh_dims=dp_dims)
                else:
                    shard_fn = _tp_shard_fn if use_tp else None
                    fully_shard(
                        model,
                        mesh=mesh,
                        reshard_after_forward=reshard,
                        shard_placement_fn=shard_fn,
                        dp_mesh_dims=dp_dims,
                    )

                if dp_pg_src is None:
                    dp_pg = mesh.get_group()
                elif dp_pg_src == "world":
                    dp_pg = dist.group.WORLD
                else:
                    dp_pg = mesh[dp_pg_src].get_group()

                replicate(
                    ref_model,
                    device_ids=[self.rank] if device_type.type != "cpu" else None,
                    process_group=dp_pg,
                )

                self._run_train_parity(
                    model, ref_model, dp_pg, mesh=mesh, mlp_dim=mlp_dim
                )
            dist.barrier()