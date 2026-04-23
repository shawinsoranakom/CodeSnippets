def forward(self, x, hint, timesteps, context, y=None, **kwargs):
        t_emb = timestep_embedding(timesteps, self.model_channels, repeat_only=False).to(x.dtype)
        emb = self.time_embed(t_emb)

        guided_hint = None
        if self.control_add_embedding is not None: #Union Controlnet
            control_type = kwargs.get("control_type", [])

            if any([c >= self.num_control_type for c in control_type]):
                max_type = max(control_type)
                max_type_name = {
                    v: k for k, v in UNION_CONTROLNET_TYPES.items()
                }[max_type]
                raise ValueError(
                    f"Control type {max_type_name}({max_type}) is out of range for the number of control types" +
                    f"({self.num_control_type}) supported.\n" +
                    "Please consider using the ProMax ControlNet Union model.\n" +
                    "https://huggingface.co/xinsir/controlnet-union-sdxl-1.0/tree/main"
                )

            emb += self.control_add_embedding(control_type, emb.dtype, emb.device)
            if len(control_type) > 0:
                if len(hint.shape) < 5:
                    hint = hint.unsqueeze(dim=0)
                guided_hint = self.union_controlnet_merge(hint, control_type, emb, context)

        if guided_hint is None:
            guided_hint = self.input_hint_block(hint, emb, context)

        out_output = []
        out_middle = []

        if self.num_classes is not None:
            if y is None:
                raise ValueError("y is None, did you try using a controlnet for SDXL on SD1?")
            emb = emb + self.label_emb(y)

        h = x
        for module, zero_conv in zip(self.input_blocks, self.zero_convs):
            if guided_hint is not None:
                h = module(h, emb, context)
                h += guided_hint
                guided_hint = None
            else:
                h = module(h, emb, context)
            out_output.append(zero_conv(h, emb, context))

        h = self.middle_block(h, emb, context)
        out_middle.append(self.middle_block_out(h, emb, context))

        return {"middle": out_middle, "output": out_output}