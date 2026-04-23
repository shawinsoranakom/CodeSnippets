def encode_token_weights(self, token_weight_pairs, template_end=-1):
        out, pooled, extra = super().encode_token_weights(token_weight_pairs)
        tok_pairs = token_weight_pairs["qwen25_7b"][0]
        count_im_start = 0
        if template_end == -1:
            for i, v in enumerate(tok_pairs):
                elem = v[0]
                if not torch.is_tensor(elem):
                    if isinstance(elem, numbers.Integral):
                        if elem == 151644 and count_im_start < 2:
                            template_end = i
                            count_im_start += 1

            if out.shape[1] > (template_end + 3):
                if tok_pairs[template_end + 1][0] == 872:
                    if tok_pairs[template_end + 2][0] == 198:
                        template_end += 3

        out = out[:, template_end:]

        extra["attention_mask"] = extra["attention_mask"][:, template_end:]
        if extra["attention_mask"].sum() == torch.numel(extra["attention_mask"]):
            extra.pop("attention_mask")  # attention mask is useless if no masked elements

        return out, pooled, extra