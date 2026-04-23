def tokenize_with_weights(self, text, return_word_ids=False, llama_template=None, images=[], prevent_empty_text=False, **kwargs):
        skip_template = False
        if text.startswith('<|im_start|>'):
            skip_template = True
        if text.startswith('<|start_header_id|>'):
            skip_template = True
        if prevent_empty_text and text == '':
            text = ' '

        if skip_template:
            llama_text = text
        else:
            if llama_template is None:
                if len(images) > 0:
                    llama_text = self.llama_template_images.format(text)
                else:
                    llama_text = self.llama_template.format(text)
            else:
                llama_text = llama_template.format(text)
        tokens = super().tokenize_with_weights(llama_text, return_word_ids=return_word_ids, disable_weights=True, **kwargs)
        key_name = next(iter(tokens))
        embed_count = 0
        qwen_tokens = tokens[key_name]
        for r in qwen_tokens:
            for i in range(len(r)):
                if r[i][0] == 151655:
                    if len(images) > embed_count:
                        r[i] = ({"type": "image", "data": images[embed_count], "original_type": "image"},) + r[i][1:]
                        embed_count += 1
        return tokens