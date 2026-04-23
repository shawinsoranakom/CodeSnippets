def test_rank0_broadcast_meta_device_init(self):
        model_args = ModelArgs(dropout_p=0.0)
        # Assume we have a CPU full state dict on rank 0
        if self.rank == 0:
            torch.manual_seed(42)
            ref_model = Transformer(model_args)
            full_sd = ref_model.state_dict()
            for param in full_sd.values():
                self.assertEqual(param.device, torch.device("cpu"))

        # Initialize the sharded model on meta device
        fsdp_mesh = init_device_mesh(device_type.type, (self.world_size,))
        with torch.device("meta"):
            model = Transformer(model_args)
        for module in model.modules():
            if isinstance(module, TransformerBlock):
                fully_shard(module, mesh=fsdp_mesh)
        fully_shard(model, mesh=fsdp_mesh)
        for param in model.parameters():
            self.assertEqual(param.device, torch.device("meta"))

        # Construct a sharded state dict from the rank 0 full state dict by
        # broadcasting and sharding
        meta_sharded_sd = model.state_dict()
        sharded_sd = {}
        if self.rank == 0:
            self.assertEqual(len(meta_sharded_sd), len(full_sd))
            self.assertEqual(list(meta_sharded_sd.keys()), list(full_sd.keys()))
            for (param_name, full_param), sharded_meta_param in zip(
                full_sd.items(), meta_sharded_sd.values()
            ):
                full_param = full_param.detach().to(device_type)
                mesh = sharded_meta_param.device_mesh
                dist.broadcast(full_param, src=0, group=mesh.get_group(0))
                sharded_tensor = distribute_tensor(
                    full_param, mesh, sharded_meta_param.placements
                )
                sharded_sd[param_name] = nn.Parameter(sharded_tensor)
        else:
            for param_name, sharded_meta_param in meta_sharded_sd.items():
                full_tensor = torch.empty(
                    sharded_meta_param.size(),
                    device=device_type.type,
                    dtype=sharded_meta_param.dtype,
                )
                mesh = sharded_meta_param.device_mesh
                dist.broadcast(full_tensor, src=0, group=mesh.get_group(0))
                sharded_tensor = distribute_tensor(
                    full_tensor, mesh, sharded_meta_param.placements
                )
                sharded_sd[param_name] = nn.Parameter(sharded_tensor)

        model.load_state_dict(sharded_sd, assign=True)
        for param in model.parameters():
            self.assertIsInstance(param, DTensor)
            self.assertEqual(param.device.type, device_type.type)

        # Construct the reference model on nonzero ranks by broadcasting the
        # unsharded model from rank 0 and sharding on all ranks
        if self.rank != 0:
            ref_model = Transformer(model_args)
        for param in ref_model.parameters():
            torch.distributed.broadcast(param.detach(), src=0)
        for module in ref_model.modules():
            if isinstance(module, TransformerBlock):
                fully_shard(module, mesh=fsdp_mesh)
        fully_shard(ref_model, mesh=fsdp_mesh)

        for (param_name, param), (ref_param_name, ref_param) in zip(
            model.named_parameters(), ref_model.named_parameters()
        ):
            self.assertEqual(param_name, ref_param_name)
            self.assertEqual(param, ref_param)

        # Check one forward/backward for parity
        inp = torch.randint(0, model_args.vocab_size, (2, 16), device=device_type.type)
        loss = model(inp).sum()
        loss.backward()
        ref_loss = ref_model(inp).sum()
        ref_loss.backward()
        self.assertEqual(loss, ref_loss)
        for param, ref_param in zip(model.parameters(), ref_model.parameters()):
            self.assertEqual(param.grad, ref_param.grad)