def test_rank0_offload_full_state_dict(self):
        # Construct a reference unsharded model on all ranks
        model_args = ModelArgs(dropout_p=0.0)
        torch.manual_seed(42)
        ref_model = Transformer(model_args).to(device_type)
        for param in ref_model.parameters():
            torch.distributed.broadcast(param.detach(), src=0)

        # Construct a sharded model and sharded state dict on all ranks
        model = copy.deepcopy(ref_model)
        for module in model.modules():
            if isinstance(module, TransformerBlock):
                fully_shard(module)
        fully_shard(model)
        sharded_sd = model.state_dict()

        # Save a reference CPU full state dict on rank 0 and delete the
        # reference model otherwise
        if self.rank != 0:
            del ref_model
        else:
            ref_gpu_full_sd = ref_model.state_dict()
            ref_full_sd = {k: v.cpu() for k, v in ref_gpu_full_sd.items()}
            del ref_gpu_full_sd

        # Reshard the GPU sharded state dict to a CPU full state dict on rank 0
        full_sd = {}
        for param_name, sharded_param in sharded_sd.items():
            full_param = sharded_param.full_tensor()
            if self.rank == 0:
                full_sd[param_name] = full_param.cpu()
            else:
                del full_param

        # Check that we have a CPU full state dict only on rank 0
        if self.rank == 0:
            self.assertEqual(len(full_sd), len(ref_full_sd))
            self.assertEqual(list(full_sd.keys()), list(ref_full_sd.keys()))
            for param, ref_param in zip(
                full_sd.values(), ref_full_sd.values(), strict=True
            ):
                self.assertEqual(param.device, torch.device("cpu"))
                self.assertEqual(param.device, ref_param.device)
                self.assertEqual(param, ref_param)
        else:
            self.assertEqual(len(full_sd), 0)