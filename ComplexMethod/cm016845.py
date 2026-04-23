def attention_multiply(attn, model, q, k, v, out):
    m = model.clone()
    sd = model.model_state_dict()

    for key in sd:
        if key.endswith("{}.to_q.bias".format(attn)) or key.endswith("{}.to_q.weight".format(attn)):
            m.add_patches({key: (None,)}, 0.0, q)
        if key.endswith("{}.to_k.bias".format(attn)) or key.endswith("{}.to_k.weight".format(attn)):
            m.add_patches({key: (None,)}, 0.0, k)
        if key.endswith("{}.to_v.bias".format(attn)) or key.endswith("{}.to_v.weight".format(attn)):
            m.add_patches({key: (None,)}, 0.0, v)
        if key.endswith("{}.to_out.0.bias".format(attn)) or key.endswith("{}.to_out.0.weight".format(attn)):
            m.add_patches({key: (None,)}, 0.0, out)

    return m