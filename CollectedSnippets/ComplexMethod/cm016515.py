def load_gligen(sd):
    sd_k = sd.keys()
    output_list = []
    key_dim = 768
    for a in ["input_blocks", "middle_block", "output_blocks"]:
        for b in range(20):
            k_temp = filter(lambda k: "{}.{}.".format(a, b)
                            in k and ".fuser." in k, sd_k)
            k_temp = map(lambda k: (k, k.split(".fuser.")[-1]), k_temp)

            n_sd = {}
            for k in k_temp:
                n_sd[k[1]] = sd[k[0]]
            if len(n_sd) > 0:
                query_dim = n_sd["linear.weight"].shape[0]
                key_dim = n_sd["linear.weight"].shape[1]

                if key_dim == 768:  # SD1.x
                    n_heads = 8
                    d_head = query_dim // n_heads
                else:
                    d_head = 64
                    n_heads = query_dim // d_head

                gated = GatedSelfAttentionDense(
                    query_dim, key_dim, n_heads, d_head)
                gated.load_state_dict(n_sd, strict=False)
                output_list.append(gated)

    if "position_net.null_positive_feature" in sd_k:
        in_dim = sd["position_net.null_positive_feature"].shape[0]
        out_dim = sd["position_net.linears.4.weight"].shape[0]

        class WeightsLoader(torch.nn.Module):
            pass
        w = WeightsLoader()
        w.position_net = PositionNet(in_dim, out_dim)
        w.load_state_dict(sd, strict=False)

    gligen = Gligen(output_list, w.position_net, key_dim)
    return gligen