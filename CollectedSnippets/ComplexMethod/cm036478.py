def test_ep2_rank0_gets_half_experts(self, synthetic_moe_files):
        files, expected = synthetic_moe_files
        # EP=2, rank=0 → experts 0-3
        local_ids = compute_local_expert_ids(8, ep_size=2, ep_rank=0)
        loaded = dict(
            safetensors_weights_iterator(files, False, local_expert_ids=local_ids)
        )

        # Should have all dense + shared + experts 0-3 only
        for name in loaded:
            eid = parse_expert_id(name)
            if eid is not None:
                assert eid in local_ids, f"Non-local expert {eid} was loaded"

        # Check expert count: 4 experts × 3 weights = 12
        expert_names = [n for n in loaded if parse_expert_id(n) is not None]
        assert len(expert_names) == 4 * 3

        # Check all dense weights present
        assert "model.embed_tokens.weight" in loaded
        assert "model.layers.0.self_attn.q_proj.weight" in loaded
        assert "model.layers.0.input_layernorm.weight" in loaded
        assert "model.layers.0.mlp.shared_experts.gate_proj.weight" in loaded