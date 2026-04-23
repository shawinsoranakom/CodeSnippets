def test_hsdp_broadcast_across_replicas(self):
        shard_size, replicate_size = 2, 2
        mesh = init_device_mesh(
            device_type.type,
            (replicate_size, shard_size),
            mesh_dim_names=("replicate", "shard"),
        )
        model_args = ModelArgs()
        model = Transformer(model_args)
        # Add a buffer to show that this flow works for buffers too
        model.buf = torch.nn.Buffer(torch.randn((model_args.dim,)))
        for module in model.modules():
            if isinstance(module, TransformerBlock):
                fully_shard(module, mesh=mesh)
        fully_shard(model, mesh=mesh)

        # Only preserve the model states on the replicate mesh's rank 0
        if mesh.get_local_rank("replicate") > 0:
            for tensor in itertools.chain(model.parameters(), model.buffers()):
                tensor.detach().fill_(1337)

        # Check that replicas are different
        for tensor in itertools.chain(model.parameters(), model.buffers()):
            local_tensor = tensor.to_local() if isinstance(tensor, DTensor) else tensor
            local_tensor_list = [
                torch.empty_like(local_tensor) for _ in range(mesh["replicate"].size())
            ]
            dist.all_gather(
                local_tensor_list, local_tensor, group=mesh.get_group("replicate")
            )
            for other_local_tensor in local_tensor_list[1:]:
                self.assertEqual(other_local_tensor.shape, local_tensor_list[0].shape)
                self.assertNotEqual(other_local_tensor, local_tensor_list[0])

        # Broadcast from replicate mesh's rank 0
        replicate_group = mesh.get_group("replicate")
        for tensor in itertools.chain(model.parameters(), model.buffers()):
            # E.g. for mesh [[0, 1, 2, 3], [4, 5, 6, 7]] sharding on dim-1 and
            # replicating on dim-0, broadcast with sources 0, 1, 2, 3
            src_rank = dist.get_process_group_ranks(replicate_group)[0]
            torch.distributed.broadcast(
                tensor.to_local() if isinstance(tensor, DTensor) else tensor,
                src=src_rank,
                group=replicate_group,
            )

        # Check that replicas are the same
        for tensor in itertools.chain(model.parameters(), model.buffers()):
            local_tensor = tensor.to_local() if isinstance(tensor, DTensor) else tensor
            local_tensor_list = [
                torch.empty_like(local_tensor) for _ in range(mesh["replicate"].size())
            ]
            dist.all_gather(
                local_tensor_list, local_tensor, group=mesh.get_group("replicate")
            )
            for other_local_tensor in local_tensor_list[1:]:
                self.assertEqual(other_local_tensor, local_tensor_list[0])

        # Check that we can run an iteration without erroring
        inp = torch.randint(0, model_args.vocab_size, (2, 16), device=device_type.type)
        model(inp).sum().backward()