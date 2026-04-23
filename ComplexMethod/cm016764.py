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

        if template_end == -1:
            template_end = 0

        suffix_start = None
        for i in range(len(tok_pairs) - 1, -1, -1):
            elem = tok_pairs[i][0]
            if not torch.is_tensor(elem) and isinstance(elem, numbers.Integral):
                if elem == 151645:
                    suffix_start = i
                    break

        out = out[:, template_end:]

        if "attention_mask" in extra:
            extra["attention_mask"] = extra["attention_mask"][:, template_end:]
            if extra["attention_mask"].sum() == torch.numel(extra["attention_mask"]):
                extra.pop("attention_mask")

        if suffix_start is not None:
            suffix_len = len(tok_pairs) - suffix_start
            if suffix_len > 0 and out.shape[1] > suffix_len:
                out = out[:, :-suffix_len]
                if "attention_mask" in extra:
                    extra["attention_mask"] = extra["attention_mask"][:, :-suffix_len]
                    if extra["attention_mask"].sum() == torch.numel(
                        extra["attention_mask"]
                    ):
                        extra.pop("attention_mask")

        return out, pooled, extra