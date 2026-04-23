def encode_token_weights(self, token_weight_pairs):
        token_weight_pairs_l = token_weight_pairs["l"]
        token_weight_pairs_llama = token_weight_pairs["llama"]

        llama_out, llama_pooled, llama_extra_out = self.llama.encode_token_weights(token_weight_pairs_llama)

        template_end = 0
        extra_template_end = 0
        extra_sizes = 0
        user_end = 9999999999999
        images = []

        tok_pairs = token_weight_pairs_llama[0]
        for i, v in enumerate(tok_pairs):
            elem = v[0]
            if not torch.is_tensor(elem):
                if isinstance(elem, numbers.Integral):
                    if elem == 128006:
                        if tok_pairs[i + 1][0] == 882:
                            if tok_pairs[i + 2][0] == 128007:
                                template_end = i + 2
                                user_end = -1
                    if elem == 128009 and user_end == -1:
                        user_end = i + 1
                else:
                    if elem.get("original_type") == "image":
                        elem_size = elem.get("data").shape[0]
                        if template_end > 0:
                            if user_end == -1:
                                extra_template_end += elem_size - 1
                        else:
                            image_start = i + extra_sizes
                            image_end = i + elem_size + extra_sizes
                            images.append((image_start, image_end, elem.get("image_interleave", 1)))
                            extra_sizes += elem_size - 1

        if llama_out.shape[1] > (template_end + 2):
            if tok_pairs[template_end + 1][0] == 271:
                template_end += 2
        llama_output = llama_out[:, template_end + extra_sizes:user_end + extra_sizes + extra_template_end]
        llama_extra_out["attention_mask"] = llama_extra_out["attention_mask"][:, template_end + extra_sizes:user_end + extra_sizes + extra_template_end]
        if llama_extra_out["attention_mask"].sum() == torch.numel(llama_extra_out["attention_mask"]):
            llama_extra_out.pop("attention_mask")  # attention mask is useless if no masked elements

        if len(images) > 0:
            out = []
            for i in images:
                out.append(llama_out[:, i[0]: i[1]: i[2]])
            llama_output = torch.cat(out + [llama_output], dim=1)

        l_out, l_pooled = self.clip_l.encode_token_weights(token_weight_pairs_l)
        return llama_output, l_pooled, llama_extra_out