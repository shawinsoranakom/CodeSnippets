def tokenize_with_weights(self, text, return_word_ids=False, images=None, **kwargs):
        skip_template = False
        if text.startswith("<|im_start|>"):
            skip_template = True
        if text.startswith("<|start_header_id|>"):
            skip_template = True
        if text == "":
            text = " "

        base_tok = getattr(self, "qwen25_7b")
        if skip_template:
            tokens = super().tokenize_with_weights(
                text, return_word_ids=return_word_ids, disable_weights=True, **kwargs
            )
        else:
            has_images = images is not None and len(images) > 0
            template_prefix = self.EDIT_PREFIX if has_images else self.T2I_PREFIX

            prefix_ids = base_tok.tokenizer(
                template_prefix, add_special_tokens=False
            )["input_ids"]
            suffix_ids = base_tok.tokenizer(
                self.SUFFIX, add_special_tokens=False
            )["input_ids"]

            prompt_tokens = base_tok.tokenize_with_weights(
                text, return_word_ids=return_word_ids, **kwargs
            )
            prompt_pairs = prompt_tokens[0]

            prefix_pairs = [(t, 1.0) for t in prefix_ids]
            suffix_pairs = [(t, 1.0) for t in suffix_ids]

            combined = prefix_pairs + prompt_pairs + suffix_pairs

            if has_images:
                embed_count = 0
                for i in range(len(combined)):
                    if combined[i][0] == IMAGE_PAD_TOKEN_ID and embed_count < len(images):
                        combined[i] = ({"type": "image", "data": images[embed_count], "original_type": "image"}, combined[i][1])
                        embed_count += 1

            tokens = {"qwen25_7b": [combined]}

        return tokens