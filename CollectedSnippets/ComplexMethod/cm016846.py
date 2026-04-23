def execute(cls, clip, q, k, v, out) -> io.NodeOutput:
        m = clip.clone()
        sd = m.patcher.model_state_dict()

        for key in sd:
            if key.endswith("self_attn.q_proj.weight") or key.endswith("self_attn.q_proj.bias"):
                m.add_patches({key: (None,)}, 0.0, q)
            if key.endswith("self_attn.k_proj.weight") or key.endswith("self_attn.k_proj.bias"):
                m.add_patches({key: (None,)}, 0.0, k)
            if key.endswith("self_attn.v_proj.weight") or key.endswith("self_attn.v_proj.bias"):
                m.add_patches({key: (None,)}, 0.0, v)
            if key.endswith("self_attn.out_proj.weight") or key.endswith("self_attn.out_proj.bias"):
                m.add_patches({key: (None,)}, 0.0, out)
        return io.NodeOutput(m)