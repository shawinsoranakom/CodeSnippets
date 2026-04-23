def _fuse_moe_quant_states(self, model: nn.Module, quant_states_dict: dict) -> dict:
        """

        This function consolidates individual expert quantization states into
        fused representations for w13 and w2.
        """
        from bitsandbytes.functional import QuantState

        if not self.expert_params_mapping:
            return dict()

        expert_mapping = self.expert_params_mapping
        expert_qs_dict = {}
        for name, module in model.named_modules():
            if not isinstance(module, FusedMoE):
                continue
            w1_states_lst = []
            w2_states_lst = []
            w3_states_lst = []
            for exp in expert_mapping:
                shard_id = exp[-1]
                if shard_id not in ("w1", "w2", "w3"):
                    raise ValueError(
                        f"shard_id must be ['w1','w2','w3'] but got {shard_id}."
                    )
                layer_prefix = name.split("experts")[0]
                weight_qual_name = layer_prefix + exp[1] + "weight"
                quant_state = self._dequantize_dq(quant_states_dict[weight_qual_name])
                if shard_id == "w1":
                    w1_states_lst.append(quant_state)
                elif shard_id == "w2":
                    w2_states_lst.append(quant_state)
                else:
                    w3_states_lst.append(quant_state)
                del quant_states_dict[weight_qual_name]
            assert len(w1_states_lst) == len(w2_states_lst) == len(w3_states_lst)
            w13_absmax_lst = []
            w2_absmax_lst = []
            w13_total_dim0 = 0
            w2_total_dim0 = 0
            for w1_qs, w2_qs, w3_qs in zip(w1_states_lst, w2_states_lst, w3_states_lst):
                assert w1_qs.shape == w3_qs.shape
                assert w1_qs.blocksize == w2_qs.blocksize == w3_qs.blocksize
                assert w1_qs.dtype == w2_qs.dtype == w3_qs.dtype
                # w1 and w3 are interleaved in storage
                w13_absmax_lst.append(w1_qs.absmax)
                w13_absmax_lst.append(w3_qs.absmax)
                w2_absmax_lst.append(w2_qs.absmax)
                w13_total_dim0 += w1_qs.shape[0] + w3_qs.shape[0]
                w2_total_dim0 += w2_qs.shape[0]

            w13_absmax = torch.cat(w13_absmax_lst)
            w2_absmax = torch.cat(w2_absmax_lst)
            # Create fused quantization state for w13.
            w13_qs = QuantState(
                absmax=w13_absmax,
                shape=(w13_total_dim0, w1_states_lst[0].shape[1]),
                code=w1_states_lst[0].code,
                blocksize=w1_states_lst[0].blocksize,
                quant_type="nf4",
                dtype=w1_states_lst[0].dtype,
            )
            # Create fused quantization state for w2.
            w2_qs = QuantState(
                absmax=w2_absmax,
                shape=(w2_total_dim0, w2_states_lst[0].shape[1]),
                code=w2_states_lst[0].code,
                blocksize=w2_states_lst[0].blocksize,
                quant_type="nf4",
                dtype=w2_states_lst[0].dtype,
            )
            # The weight suffixes .w13_weight and .w2_weight are consistent
            # with the param in BitsAndBytesMoEMethod.
            w13_weight_name = name + ".w13_weight"
            w2_weight_name = name + ".w2_weight"
            expert_qs_dict[w13_weight_name] = w13_qs
            expert_qs_dict[w2_weight_name] = w2_qs
        return expert_qs_dict