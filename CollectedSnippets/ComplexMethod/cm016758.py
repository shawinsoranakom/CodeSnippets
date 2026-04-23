def encode_token_weights(self, token_weight_pairs, template_end=-1):
        out, pooled = super().encode_token_weights(token_weight_pairs)
        tok_pairs = token_weight_pairs["qwen3_2b"][0]
        count_im_start = 0
        if template_end == -1:
            for i, v in enumerate(tok_pairs):
                elem = v[0]
                if not torch.is_tensor(elem):
                    if isinstance(elem, numbers.Integral):
                        if elem == 4004 and count_im_start < 1:
                            template_end = i
                            count_im_start += 1

            if out.shape[1] > (template_end + 1):
                if tok_pairs[template_end + 1][0] == 25:
                    template_end += 1

        out = out[:, template_end:]
        return out, pooled, {}