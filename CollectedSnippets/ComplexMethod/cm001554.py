def forward(self, texts):
        """
        Accepts an array of texts; Passes texts through transformers network to create a tensor with numerical representation of those texts.
        Returns a tensor with shape of (B, T, C), where B is length of the array; T is length, in tokens, of texts (including padding) - T will
        be a multiple of 77; and C is dimensionality of each token - for SD1 it's 768, for SD2 it's 1024, and for SDXL it's 1280.
        An example shape returned by this function can be: (2, 77, 768).
        For SDXL, instead of returning one tensor avobe, it returns a tuple with two: the other one with shape (B, 1280) with pooled values.
        Webui usually sends just one text at a time through this function - the only time when texts is an array with more than one element
        is when you do prompt editing: "a picture of a [cat:dog:0.4] eating ice cream"
        """

        batch_chunks, token_count = self.process_texts(texts)

        used_embeddings = {}
        chunk_count = max([len(x) for x in batch_chunks])

        zs = []
        for i in range(chunk_count):
            batch_chunk = [chunks[i] if i < len(chunks) else self.empty_chunk() for chunks in batch_chunks]

            tokens = [x.tokens for x in batch_chunk]
            multipliers = [x.multipliers for x in batch_chunk]
            self.hijack.fixes = [x.fixes for x in batch_chunk]

            for fixes in self.hijack.fixes:
                for _position, embedding in fixes:
                    used_embeddings[embedding.name] = embedding
            devices.torch_npu_set_device()
            z = self.process_tokens(tokens, multipliers)
            zs.append(z)

        if opts.textual_inversion_add_hashes_to_infotext and used_embeddings:
            hashes = []
            for name, embedding in used_embeddings.items():
                shorthash = embedding.shorthash
                if not shorthash:
                    continue

                name = name.replace(":", "").replace(",", "")
                hashes.append(f"{name}: {shorthash}")

            if hashes:
                if self.hijack.extra_generation_params.get("TI hashes"):
                    hashes.append(self.hijack.extra_generation_params.get("TI hashes"))
                self.hijack.extra_generation_params["TI hashes"] = ", ".join(hashes)

        if any(x for x in texts if "(" in x or "[" in x) and opts.emphasis != "Original":
            self.hijack.extra_generation_params["Emphasis"] = opts.emphasis

        if self.return_pooled:
            return torch.hstack(zs), zs[0].pooled
        else:
            return torch.hstack(zs)