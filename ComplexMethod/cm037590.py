def weight_loader(self, param: Parameter, loaded_weight: torch.Tensor):
        output_dim = getattr(param, "output_dim", None)
        packed_dim = getattr(param, "packed_dim", None)

        # If the parameter is a gguf weight, then load it directly.
        if getattr(param, "is_gguf_weight_type", None):
            param.data.copy_(loaded_weight)
            param.weight_type = loaded_weight.item()
            return
        elif isinstance(param, UninitializedParameter):
            shape = list(loaded_weight.shape)
            if output_dim is not None:
                shape[output_dim] = self.num_embeddings_per_partition
            param.materialize(tuple(shape), dtype=loaded_weight.dtype)

        # If parameter does not have output dim, then it should
        # be copied onto all gpus (e.g. g_idx for act_order gptq).
        if output_dim is None:
            assert param.data.shape == loaded_weight.shape
            param.data.copy_(loaded_weight)
            return

        # Shard indexes for loading the weight
        start_idx = self.shard_indices.org_vocab_start_index
        shard_size = self.shard_indices.org_vocab_end_index - start_idx

        # If param packed on the same dim we are sharding on, then
        # need to adjust offsets of loaded weight by pack_factor.
        if packed_dim is not None and packed_dim == output_dim:
            packed_factor = (
                param.packed_factor
                if isinstance(param, BasevLLMParameter)
                else param.pack_factor
            )
            assert loaded_weight.shape[output_dim] == (
                self.org_vocab_size // param.packed_factor
            )
            start_idx = start_idx // packed_factor
            shard_size = shard_size // packed_factor
        else:
            assert loaded_weight.shape[output_dim] == self.org_vocab_size

        # Copy the data. Select chunk corresponding to current shard.
        loaded_weight = loaded_weight.narrow(output_dim, start_idx, shard_size)
        param[: loaded_weight.shape[0]].data.copy_(loaded_weight)
        param[loaded_weight.shape[0] :].data.fill_(0)