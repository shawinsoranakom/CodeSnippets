def tokenize_with_weights(self, text, return_word_ids=False, image=None, llama_template=None, skip_template=True, **kwargs):
        self.llama_template = "<start_of_turn>system\nYou are a helpful assistant.<end_of_turn>\n<start_of_turn>user\n{}<end_of_turn>\n<start_of_turn>model\n"
        self.llama_template_images = "<start_of_turn>system\nYou are a helpful assistant.<end_of_turn>\n<start_of_turn>user\n\n<image_soft_token>{}<end_of_turn>\n\n<start_of_turn>model\n"

        if image is None:
            images = []
        else:
            samples = image.movedim(-1, 1)
            total = int(896 * 896)

            scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
            width = round(samples.shape[3] * scale_by)
            height = round(samples.shape[2] * scale_by)

            s = comfy.utils.common_upscale(samples, width, height, "area", "disabled").movedim(1, -1)
            images = [s[:, :, :, :3]]

        if text.startswith('<start_of_turn>'):
            skip_template = True

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

        text_tokens = super().tokenize_with_weights(llama_text, return_word_ids)

        if len(images) > 0:
            embed_count = 0
            for r in text_tokens:
                for i, token in enumerate(r):
                    if token[0] == 262144 and embed_count < len(images):
                        r[i] = ({"type": "image", "data": images[embed_count]},) + token[1:]
                        embed_count += 1
        return text_tokens