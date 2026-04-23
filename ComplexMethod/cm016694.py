def forward_orig(
        self,
        img: Tensor,
        img_ids: Tensor,
        txt: Tensor,
        txt_ids: Tensor,
        timesteps: Tensor,
        y: Tensor,
        guidance: Tensor = None,
        control = None,
        timestep_zero_index=None,
        transformer_options={},
        attn_mask: Tensor = None,
    ) -> Tensor:

        transformer_options = transformer_options.copy()
        patches = transformer_options.get("patches", {})
        patches_replace = transformer_options.get("patches_replace", {})
        if img.ndim != 3 or txt.ndim != 3:
            raise ValueError("Input img and txt tensors must have 3 dimensions.")

        # running on sequences img
        img = self.img_in(img)
        vec = self.time_in(timestep_embedding(timesteps, 256).to(img.dtype))
        if self.params.guidance_embed:
            if guidance is not None:
                vec = vec + self.guidance_in(timestep_embedding(guidance, 256).to(img.dtype))

        if self.vector_in is not None:
            if y is None:
                y = torch.zeros((img.shape[0], self.params.vec_in_dim), device=img.device, dtype=img.dtype)
            vec = vec + self.vector_in(y[:, :self.params.vec_in_dim])

        if self.txt_norm is not None:
            txt = self.txt_norm(txt)
        txt = self.txt_in(txt)

        if "post_input" in patches:
            for p in patches["post_input"]:
                out = p({"img": img, "txt": txt, "img_ids": img_ids, "txt_ids": txt_ids, "transformer_options": transformer_options})
                img = out["img"]
                txt = out["txt"]
                img_ids = out["img_ids"]
                txt_ids = out["txt_ids"]

        if img_ids is not None:
            ids = torch.cat((txt_ids, img_ids), dim=1)
            pe = self.pe_embedder(ids)
        else:
            pe = None

        vec_orig = vec
        txt_vec = vec
        extra_kwargs = {}
        if timestep_zero_index is not None:
            modulation_dims = []
            batch = vec.shape[0] // 2
            vec_orig = vec_orig.reshape(2, batch, vec.shape[1]).movedim(0, 1)
            invert = invert_slices(timestep_zero_index, img.shape[1])
            for s in invert:
                modulation_dims.append((s[0], s[1], 0))
            for s in timestep_zero_index:
                modulation_dims.append((s[0], s[1], 1))
            extra_kwargs["modulation_dims_img"] = modulation_dims
            txt_vec = vec[:batch]

        if self.params.global_modulation:
            vec = (self.double_stream_modulation_img(vec_orig), self.double_stream_modulation_txt(txt_vec))

        blocks_replace = patches_replace.get("dit", {})
        transformer_options["total_blocks"] = len(self.double_blocks)
        transformer_options["block_type"] = "double"
        for i, block in enumerate(self.double_blocks):
            transformer_options["block_index"] = i
            if ("double_block", i) in blocks_replace:
                def block_wrap(args):
                    out = {}
                    out["img"], out["txt"] = block(img=args["img"],
                                                   txt=args["txt"],
                                                   vec=args["vec"],
                                                   pe=args["pe"],
                                                   attn_mask=args.get("attn_mask"),
                                                   transformer_options=args.get("transformer_options"),
                                                   **extra_kwargs)
                    return out

                out = blocks_replace[("double_block", i)]({"img": img,
                                                           "txt": txt,
                                                           "vec": vec,
                                                           "pe": pe,
                                                           "attn_mask": attn_mask,
                                                           "transformer_options": transformer_options},
                                                          {"original_block": block_wrap})
                txt = out["txt"]
                img = out["img"]
            else:
                img, txt = block(img=img,
                                 txt=txt,
                                 vec=vec,
                                 pe=pe,
                                 attn_mask=attn_mask,
                                 transformer_options=transformer_options,
                                 **extra_kwargs)

            if control is not None: # Controlnet
                control_i = control.get("input")
                if i < len(control_i):
                    add = control_i[i]
                    if add is not None:
                        img[:, :add.shape[1]] += add

        if img.dtype == torch.float16:
            img = torch.nan_to_num(img, nan=0.0, posinf=65504, neginf=-65504)

        img = torch.cat((txt, img), 1)

        if self.params.global_modulation:
            vec, _ = self.single_stream_modulation(vec_orig)

        extra_kwargs = {}
        if timestep_zero_index is not None:
            lambda a: 0 if a == 0 else a + txt.shape[1]
            modulation_dims_combined = list(map(lambda x: (0 if x[0] == 0 else x[0] + txt.shape[1], x[1] + txt.shape[1], x[2]), modulation_dims))
            extra_kwargs["modulation_dims"] = modulation_dims_combined

        transformer_options["total_blocks"] = len(self.single_blocks)
        transformer_options["block_type"] = "single"
        transformer_options["img_slice"] = [txt.shape[1], img.shape[1]]
        for i, block in enumerate(self.single_blocks):
            transformer_options["block_index"] = i
            if ("single_block", i) in blocks_replace:
                def block_wrap(args):
                    out = {}
                    out["img"] = block(args["img"],
                                       vec=args["vec"],
                                       pe=args["pe"],
                                       attn_mask=args.get("attn_mask"),
                                       transformer_options=args.get("transformer_options"),
                                       **extra_kwargs)
                    return out

                out = blocks_replace[("single_block", i)]({"img": img,
                                                           "vec": vec,
                                                           "pe": pe,
                                                           "attn_mask": attn_mask,
                                                           "transformer_options": transformer_options},
                                                          {"original_block": block_wrap})
                img = out["img"]
            else:
                img = block(img, vec=vec, pe=pe, attn_mask=attn_mask, transformer_options=transformer_options, **extra_kwargs)

            if control is not None: # Controlnet
                control_o = control.get("output")
                if i < len(control_o):
                    add = control_o[i]
                    if add is not None:
                        img[:, txt.shape[1] : txt.shape[1] + add.shape[1], ...] += add

        img = img[:, txt.shape[1] :, ...]

        extra_kwargs = {}
        if timestep_zero_index is not None:
            extra_kwargs["modulation_dims"] = modulation_dims

        img = self.final_layer(img, vec_orig, **extra_kwargs)  # (N, T, patch_size ** 2 * out_channels)
        return img