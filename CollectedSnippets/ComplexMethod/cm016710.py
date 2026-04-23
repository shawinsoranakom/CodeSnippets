def forward_orig(
        self,
        img: Tensor,
        img_ids: Tensor,
        txt: Tensor,
        txt_ids: Tensor,
        timesteps: Tensor,
        guidance: Tensor = None,
        control = None,
        transformer_options={},
        attn_mask: Tensor = None,
    ) -> Tensor:
        transformer_options = transformer_options.copy()
        patches_replace = transformer_options.get("patches_replace", {})

        # running on sequences img
        img = self.img_in(img)

        # distilled vector guidance
        mod_index_length = 344
        distill_timestep = timestep_embedding(timesteps.detach().clone(), 16).to(img.device, img.dtype)
        # guidance = guidance *
        distil_guidance = timestep_embedding(guidance.detach().clone(), 16).to(img.device, img.dtype)

        # get all modulation index
        modulation_index = timestep_embedding(torch.arange(mod_index_length, device=img.device), 32).to(img.device, img.dtype)
        # we need to broadcast the modulation index here so each batch has all of the index
        modulation_index = modulation_index.unsqueeze(0).repeat(img.shape[0], 1, 1).to(img.device, img.dtype)
        # and we need to broadcast timestep and guidance along too
        timestep_guidance = torch.cat([distill_timestep, distil_guidance], dim=1).unsqueeze(1).repeat(1, mod_index_length, 1).to(img.dtype).to(img.device, img.dtype)
        # then and only then we could concatenate it together
        input_vec = torch.cat([timestep_guidance, modulation_index], dim=-1).to(img.device, img.dtype)

        mod_vectors = self.distilled_guidance_layer(input_vec)

        txt = self.txt_in(txt)

        ids = torch.cat((txt_ids, img_ids), dim=1)
        pe = self.pe_embedder(ids)

        blocks_replace = patches_replace.get("dit", {})
        transformer_options["total_blocks"] = len(self.double_blocks)
        transformer_options["block_type"] = "double"
        for i, block in enumerate(self.double_blocks):
            transformer_options["block_index"] = i
            if i not in self.skip_mmdit:
                double_mod = (
                    self.get_modulations(mod_vectors, "double_img", idx=i),
                    self.get_modulations(mod_vectors, "double_txt", idx=i),
                )
                if ("double_block", i) in blocks_replace:
                    def block_wrap(args):
                        out = {}
                        out["img"], out["txt"] = block(img=args["img"],
                                                       txt=args["txt"],
                                                       vec=args["vec"],
                                                       pe=args["pe"],
                                                       attn_mask=args.get("attn_mask"),
                                                       transformer_options=args.get("transformer_options"))
                        return out

                    out = blocks_replace[("double_block", i)]({"img": img,
                                                               "txt": txt,
                                                               "vec": double_mod,
                                                               "pe": pe,
                                                               "attn_mask": attn_mask,
                                                               "transformer_options": transformer_options},
                                                              {"original_block": block_wrap})
                    txt = out["txt"]
                    img = out["img"]
                else:
                    img, txt = block(img=img,
                                     txt=txt,
                                     vec=double_mod,
                                     pe=pe,
                                     attn_mask=attn_mask,
                                     transformer_options=transformer_options)

                if control is not None: # Controlnet
                    control_i = control.get("input")
                    if i < len(control_i):
                        add = control_i[i]
                        if add is not None:
                            img += add

        img = torch.cat((txt, img), 1)

        transformer_options["total_blocks"] = len(self.single_blocks)
        transformer_options["block_type"] = "single"
        transformer_options["img_slice"] = [txt.shape[1], img.shape[1]]
        for i, block in enumerate(self.single_blocks):
            transformer_options["block_index"] = i
            if i not in self.skip_dit:
                single_mod = self.get_modulations(mod_vectors, "single", idx=i)
                if ("single_block", i) in blocks_replace:
                    def block_wrap(args):
                        out = {}
                        out["img"] = block(args["img"],
                                           vec=args["vec"],
                                           pe=args["pe"],
                                           attn_mask=args.get("attn_mask"),
                                           transformer_options=args.get("transformer_options"))
                        return out

                    out = blocks_replace[("single_block", i)]({"img": img,
                                                               "vec": single_mod,
                                                               "pe": pe,
                                                               "attn_mask": attn_mask,
                                                               "transformer_options": transformer_options},
                                                              {"original_block": block_wrap})
                    img = out["img"]
                else:
                    img = block(img, vec=single_mod, pe=pe, attn_mask=attn_mask, transformer_options=transformer_options)

                if control is not None: # Controlnet
                    control_o = control.get("output")
                    if i < len(control_o):
                        add = control_o[i]
                        if add is not None:
                            img[:, txt.shape[1] :, ...] += add

        img = img[:, txt.shape[1] :, ...]
        if hasattr(self, "final_layer"):
            final_mod = self.get_modulations(mod_vectors, "final")
            img = self.final_layer(img, vec=final_mod)  # (N, T, patch_size ** 2 * out_channels)
        return img