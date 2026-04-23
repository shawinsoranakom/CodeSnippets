def generate_audio_codes(model, positive, negative, min_tokens=1, max_tokens=1024, seed=0, cfg_scale=2.0, temperature=0.85, top_p=0.9, top_k=0, min_p=0.000):
    positive = [[token for token, _ in inner_list] for inner_list in positive]
    positive = positive[0]

    if cfg_scale != 1.0:
        negative = [[token for token, _ in inner_list] for inner_list in negative]
        negative = negative[0]

        neg_pad = 0
        if len(negative) < len(positive):
            neg_pad = (len(positive) - len(negative))
            negative = [model.special_tokens["pad"]] * neg_pad + negative

        pos_pad = 0
        if len(negative) > len(positive):
            pos_pad = (len(negative) - len(positive))
            positive = [model.special_tokens["pad"]] * pos_pad + positive

        ids = [positive, negative]
    else:
        ids = [positive]

    return sample_manual_loop_no_classes(model, ids, cfg_scale=cfg_scale, temperature=temperature, top_p=top_p, top_k=top_k, min_p=min_p, seed=seed, min_tokens=min_tokens, max_new_tokens=max_tokens)