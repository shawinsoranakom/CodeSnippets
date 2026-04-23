def test_sibling_submesh_reconstruct_from_ancestor(self):
        """When a closure captures an FSDP submesh while a sibling mesh (the
        concatenated fsdp+tp mesh) is a graph input, the closure-captured mesh
        must be reconstructed via _get_submesh — not baked as a get_attr
        constant that breaks serialization.

        This reproduces the SimpleFSDP + TP pattern: ReplicateComputation
        captures the FSDP submesh as self.device_mesh, while parameters are
        DTensors on DeviceMesh._concatenate([fsdp_mesh, tp_mesh]). With a
        1D world mesh unflattened into (fsdp, tp), the root mesh has dim
        name 'world' — so the reconstruct_fn must find the concatenated
        ancestor (which contains 'fsdp') rather than looking only at root.
        """
        from torch._library.fake_class_registry import FakeScriptObject

        dist.destroy_process_group()
        dist.init_process_group("fake", store=FakeStore(), rank=0, world_size=8)

        try:
            # Build 1D world mesh → unflatten → (fsdp=4, tp=2)
            world_mesh = init_device_mesh(
                self.device_type, (8,), mesh_dim_names=("world",)
            )
            dense_mesh = world_mesh._unflatten(0, (4, 2), ("fsdp", "tp"))
            fsdp_mesh = dense_mesh["fsdp"]
            tp_mesh = dense_mesh["tp"]

            # Concatenate like SimpleFSDP's _distribute_dtensor does
            concat_mesh = DeviceMesh._concatenate([fsdp_mesh, tp_mesh])

            with dist.config.patch(compile_on_one_rank=True):

                def fn(local_tensor, concat_mesh_input):
                    # concat_mesh_input is a graph input (placeholder).
                    # Simulate SimpleFSDP: create DTensor on concat mesh,
                    # extract local, re-wrap on the closure-captured
                    # fsdp_mesh, then all-gather.
                    dt = DTensor.from_local(
                        local_tensor,
                        concat_mesh_input,
                        [Shard(0), Shard(1)],
                        run_check=False,
                    )
                    local = dt.to_local()
                    fsdp_dt = DTensor.from_local(
                        local, fsdp_mesh, [Shard(0)], run_check=False
                    )
                    return (
                        fsdp_dt.redistribute(fsdp_mesh, [Replicate()]).to_local().sum()
                    )

                local_t = torch.randn(4, 4)
                gm = make_fx(fn, tracing_mode="fake")(local_t, concat_mesh)

            device_mesh_getattr_count = 0
            for node in gm.graph.nodes:
                if node.op != "get_attr":
                    continue
                val = getattr(gm, node.target, None)
                if isinstance(val, FakeScriptObject):
                    val = getattr(val, "real_obj", val)
                if isinstance(val, DeviceMesh):
                    device_mesh_getattr_count += 1

            self.assertEqual(
                device_mesh_getattr_count,
                0,
                "DeviceMesh get_attr nodes found; the closure-captured FSDP "
                "submesh should be reconstructed from the tracked concatenated "
                "ancestor via _get_submesh, not baked as a constant",
            )

            submesh_ops = [
                node
                for node in gm.graph.nodes
                if node.op == "call_function" and "get_submesh" in str(node.target)
            ]
            self.assertGreater(
                len(submesh_ops),
                0,
                "Expected _get_submesh call to derive the FSDP submesh from "
                "the tracked concatenated ancestor mesh",
            )
        finally:
            dist.destroy_process_group()
            dist.init_process_group(
                "fake", store=FakeStore(), rank=0, world_size=self.world_size
            )