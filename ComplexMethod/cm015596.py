def test_no_device_mesh_getattr_in_tp_dp_joint_graph(self):
        """Backward closures of DTensor ops should not capture DeviceMesh as
        get_attr constants in the joint graph (they break AOTAutograd cache
        serialization because ProcessGroups are unpicklable)."""
        import torch.distributed.config as dist_config
        from torch._library.fake_class_registry import FakeScriptObject

        # Need world_size=4 for a 2x2 mesh; re-init the fake PG.
        dist.destroy_process_group()
        dist.init_process_group("fake", store=FakeStore(), rank=0, world_size=4)

        def _distribute_dtensor(
            tensor: DTensor,
            device_mesh: DeviceMesh,
            dp_placements: tuple[Placement, ...],
        ) -> DTensor:
            inner_spec = tensor._spec
            spanned_mesh = DeviceMesh._concatenate([device_mesh, inner_spec.mesh])
            shard_dim = dp_placements[0].dim
            split_factor = inner_spec.num_shards_map[shard_dim]
            tensor_placement = (
                (
                    _StridedShard(shard_dim, split_factor=split_factor)
                    if split_factor > 1
                    else dp_placements[0]
                ),
            ) + inner_spec.placements
            current_spec = DTensorSpec(
                mesh=device_mesh,
                placements=(Replicate(),) * len(dp_placements),
                tensor_meta=inner_spec.tensor_meta,
            )
            target_spec = DTensorSpec(
                mesh=device_mesh,
                placements=tuple(dp_placements),
                tensor_meta=inner_spec.tensor_meta,
            )
            result_tensor = redistribute_local_tensor(
                tensor._local_tensor,
                current_spec=current_spec,
                target_spec=target_spec,
            )
            return DTensor(
                result_tensor.requires_grad_(tensor.requires_grad),
                DTensorSpec(
                    mesh=spanned_mesh,
                    placements=tensor_placement,
                    tensor_meta=inner_spec.tensor_meta,
                ),
                requires_grad=tensor.requires_grad,
            )

        class ReplicateComputation(nn.Module):
            def __init__(self, device_mesh, param_sharding):
                super().__init__()
                self.device_mesh = device_mesh
                self.param_sharding = param_sharding
                self.compute_placements = [Replicate()] * device_mesh.ndim
                self.grad_placements = [Partial(reduce_op="sum")] * device_mesh.ndim

            def forward(self, x):
                non_dp_mesh_dims = x._spec.mesh.ndim - self.device_mesh.ndim
                sharded_dtensor = DTensor.from_local(
                    x.to_local(), self.device_mesh, self.param_sharding
                )
                replicated_local_tensor = sharded_dtensor.redistribute(
                    placements=self.compute_placements,
                ).to_local(grad_placements=self.grad_placements)
                non_dp_placements = tuple(x._spec.placements[-non_dp_mesh_dims:])
                non_dp_mesh_dim_names = tuple(
                    x._spec.mesh.mesh_dim_names[-non_dp_mesh_dims:]
                )
                non_dp_mesh = x._spec.mesh[non_dp_mesh_dim_names]
                return DTensor.from_local(
                    replicated_local_tensor, non_dp_mesh, non_dp_placements
                )

        param_sharding = (Shard(0),)
        wrap_idx = [0]

        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear1 = nn.Linear(16, 16, bias=False)
                self.linear2 = nn.Linear(16, 16, bias=False)

            def forward(self, x):
                return self.linear2(torch.relu(self.linear1(x))).sum()

        with dist_config.patch("compile_on_one_rank", True):
            device = torch.device(f"{self.device_type}:0")
            torch.accelerator.set_device_index(0)
            mesh_2d = init_device_mesh(
                self.device_type, (2, 2), mesh_dim_names=("fsdp", "tp")
            )
            dp_mesh = mesh_2d["fsdp"]

            with torch.device("meta"):
                model = Model()
            parallelize_module(
                model,
                mesh_2d["tp"],
                {
                    "linear1": ColwiseParallel(),
                    "linear2": RowwiseParallel(),
                },
            )
            # Apply data parallelism with parametrization
            for mod in model.modules():
                params_dict = dict(mod.named_parameters(recurse=False))
                for p_name, p in params_dict.items():
                    mod.register_parameter(
                        p_name,
                        nn.Parameter(_distribute_dtensor(p, dp_mesh, param_sharding)),
                    )
                parametrization = ReplicateComputation(dp_mesh, param_sharding)
                props = {
                    pn: property(
                        lambda self, _pn=pn: parametrization(self._parameters[_pn])
                    )
                    for pn in params_dict
                }
                idx = wrap_idx[0]
                wrap_idx[0] += 1
                cls = type(
                    f"SimpleFSDP{mod.__class__.__name__}_{idx}",
                    (mod.__class__,),
                    props,
                )
                mod.__class__ = cls
                import sys

                sys.modules[cls.__module__].__dict__[cls.__name__] = cls

            model.to_empty(device=device)
            with dist_config.patch("compile_on_one_rank", False), torch.no_grad():
                for p in model.parameters():
                    p.fill_(0.01)
            model.train()

            x = torch.randn(4, 16, device=device)
            with (
                torch._dynamo.config.patch(fake_tensor_cache_enabled=False),
                torch.fx.traceback.preserve_node_meta(),
            ):
                gm = dynamo_graph_capture_for_export(model)(x)
                tracing_context = gm.meta["tracing_context"]

            with tracing(tracing_context), ExitStack() as stack:
                jwd = aot_export_joint_with_descriptors(stack, gm, (x,))

            for node in jwd.graph_module.graph.nodes:
                if node.op != "get_attr":
                    continue
                val = getattr(jwd.graph_module, node.target, None)
                if isinstance(val, FakeScriptObject):
                    val = getattr(val, "real_obj", val)
                self.assertNotIsInstance(
                    val,
                    DeviceMesh,
                    "DeviceMesh should not appear as get_attr in the joint graph",
                )