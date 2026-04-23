def execute(cls, photomaker, image, clip, text):
        special_token = "photomaker"
        pixel_values = comfy.clip_vision.clip_preprocess(image.to(photomaker.load_device)).float()
        try:
            index = text.split(" ").index(special_token) + 1
        except ValueError:
            index = -1
        tokens = clip.tokenize(text, return_word_ids=True)
        out_tokens = {}
        for k in tokens:
            out_tokens[k] = []
            for t in tokens[k]:
                f = list(filter(lambda x: x[2] != index, t))
                while len(f) < len(t):
                    f.append(t[-1])
                out_tokens[k].append(f)

        cond, pooled = clip.encode_from_tokens(out_tokens, return_pooled=True)

        if index > 0:
            token_index = index - 1
            num_id_images = 1
            class_tokens_mask = [True if token_index <= i < token_index+num_id_images else False for i in range(77)]
            out = photomaker(id_pixel_values=pixel_values.unsqueeze(0), prompt_embeds=cond.to(photomaker.load_device),
                            class_tokens_mask=torch.tensor(class_tokens_mask, dtype=torch.bool, device=photomaker.load_device).unsqueeze(0))
        else:
            out = cond

        return io.NodeOutput([[out, {"pooled_output": pooled}]])