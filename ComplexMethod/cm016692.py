def forward_orig(
        self,
        img: Tensor,
        img_ids: Tensor,
        controlnet_cond: Tensor,
        txt: Tensor,
        txt_ids: Tensor,
        timesteps: Tensor,
        y: Tensor,
        guidance: Tensor = None,
        control_type: Tensor = None,
    ) -> Tensor:
        if img.ndim != 3 or txt.ndim != 3:
            raise ValueError("Input img and txt tensors must have 3 dimensions.")

        if y is None:
            y = torch.zeros((img.shape[0], self.params.vec_in_dim), device=img.device, dtype=img.dtype)
        else:
            y = y[:, :self.params.vec_in_dim]

        # running on sequences img
        img = self.img_in(img)

        controlnet_cond = self.pos_embed_input(controlnet_cond)
        img = img + controlnet_cond
        vec = self.time_in(timestep_embedding(timesteps, 256))
        if self.params.guidance_embed:
            vec = vec + self.guidance_in(timestep_embedding(guidance, 256))
        vec = vec + self.vector_in(y)
        txt = self.txt_in(txt)

        if self.controlnet_mode_embedder is not None and len(control_type) > 0:
            control_cond = self.controlnet_mode_embedder(torch.tensor(control_type, device=img.device), out_dtype=img.dtype).unsqueeze(0).repeat((txt.shape[0], 1, 1))
            txt = torch.cat([control_cond, txt], dim=1)
            txt_ids = torch.cat([txt_ids[:,:1], txt_ids], dim=1)

        ids = torch.cat((txt_ids, img_ids), dim=1)
        pe = self.pe_embedder(ids)

        controlnet_double = ()

        for i in range(len(self.double_blocks)):
            img, txt = self.double_blocks[i](img=img, txt=txt, vec=vec, pe=pe)
            controlnet_double = controlnet_double + (self.controlnet_blocks[i](img),)

        img = torch.cat((txt, img), 1)

        controlnet_single = ()

        for i in range(len(self.single_blocks)):
            img = self.single_blocks[i](img, vec=vec, pe=pe)
            controlnet_single = controlnet_single + (self.controlnet_single_blocks[i](img[:, txt.shape[1] :, ...]),)

        repeat = math.ceil(self.main_model_double / len(controlnet_double))
        if self.latent_input:
            out_input = ()
            for x in controlnet_double:
                    out_input += (x,) * repeat
        else:
            out_input = (controlnet_double * repeat)

        out = {"input": out_input[:self.main_model_double]}
        if len(controlnet_single) > 0:
            repeat = math.ceil(self.main_model_single / len(controlnet_single))
            out_output = ()
            if self.latent_input:
                for x in controlnet_single:
                        out_output += (x,) * repeat
            else:
                out_output = (controlnet_single * repeat)
            out["output"] = out_output[:self.main_model_single]
        return out