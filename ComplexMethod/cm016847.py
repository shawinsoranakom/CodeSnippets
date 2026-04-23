def execute(cls, model, self_structural, self_temporal, cross_structural, cross_temporal) -> io.NodeOutput:
        m = model.clone()
        sd = model.model_state_dict()

        for k in sd:
            if (k.endswith("attn1.to_out.0.bias") or k.endswith("attn1.to_out.0.weight")):
                if '.time_stack.' in k:
                    m.add_patches({k: (None,)}, 0.0, self_temporal)
                else:
                    m.add_patches({k: (None,)}, 0.0, self_structural)
            elif (k.endswith("attn2.to_out.0.bias") or k.endswith("attn2.to_out.0.weight")):
                if '.time_stack.' in k:
                    m.add_patches({k: (None,)}, 0.0, cross_temporal)
                else:
                    m.add_patches({k: (None,)}, 0.0, cross_structural)
        return io.NodeOutput(m)