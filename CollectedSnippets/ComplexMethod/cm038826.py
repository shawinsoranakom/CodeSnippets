def pack_moe(
        cls,
        loras: GenericSequence["LoRALayerWeights | None"],
        module_name: str,
        is_non_gated_moe: bool = False,
    ) -> "PackedLoRALayerWeights":
        """Pack a list of LoRAs into a single LoRA.

        If LoRA is None, it signifies that the submodule does not have a LoRA.
        """

        first_lora = next(lora for lora in loras if lora is not None)
        assert first_lora is not None
        rank = first_lora.rank
        lora_alpha = first_lora.lora_alpha
        assert len(loras) % 3 == 0
        w1_lora_a_lst = []
        w2_lora_a_lst = []
        w3_lora_a_lst = []
        w1_lora_b_lst = []
        w2_lora_b_lst = []
        w3_lora_b_lst = []
        # TODO: Consider the case where some experts don't have LoRA added.
        for eid in range(len(loras) // 3):
            w1_lora = loras[eid * 3]
            w2_lora = loras[eid * 3 + 1]
            w3_lora = loras[eid * 3 + 2]
            # For non-gated MoE, w3 is not used, so we use w1's LoRA weights
            # This is determined by checking the expert mapping (get_expert_mapping)
            # which indicates when ckpt_up_proj_name is empty.
            if w3_lora is None and is_non_gated_moe:
                w3_lora = w1_lora
            assert w1_lora is not None
            assert w2_lora is not None
            assert w3_lora is not None

            w1_lora_a_lst.append(w1_lora.lora_a)
            w2_lora_a_lst.append(w2_lora.lora_a)
            w3_lora_a_lst.append(w3_lora.lora_a)

            w1_lora_b_lst.append(w1_lora.lora_b)
            w2_lora_b_lst.append(w2_lora.lora_b)
            w3_lora_b_lst.append(w3_lora.lora_b)

        w1_lora_a = torch.stack(w1_lora_a_lst, dim=0)  # (num_experts,rank,input_size)
        w2_lora_a = torch.stack(w2_lora_a_lst, dim=0)
        w1_lora_b = torch.stack(w1_lora_b_lst, dim=0)  # (num_experts,output_size,rank)
        w2_lora_b = torch.stack(w2_lora_b_lst, dim=0)

        # All w1, w2, w3 have the same scaling factor.
        scaling = lora_alpha / rank
        last_scaling = scaling

        if is_non_gated_moe:
            # For non-gated MoE, reuse w1 tensors for w3 to avoid memory waste
            # w3_lora_a_lst and w3_lora_b_lst are not relevant in this case
            w3_lora_a = w1_lora_a
            w3_lora_b = w1_lora_b

            # For non-gated MoE, avoid double-scaling by setting w3's scaling to 1.
            last_scaling = 1.0
        else:
            w3_lora_a = torch.stack(w3_lora_a_lst, dim=0)
            w3_lora_b = torch.stack(w3_lora_b_lst, dim=0)

        obj = cls(
            module_name,
            rank,
            [lora_alpha, lora_alpha, lora_alpha],
            [w1_lora_a, w2_lora_a, w3_lora_a],
            [w1_lora_b, w2_lora_b, w3_lora_b],
            scaling=[scaling, scaling, last_scaling],
        )
        return obj