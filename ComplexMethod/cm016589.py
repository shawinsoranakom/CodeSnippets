def forward(
        self,
        x: torch.Tensor,
        timesteps: torch.Tensor,
        y: Optional[torch.Tensor] = None,
        context: Optional[torch.Tensor] = None,
        hint = None,
    ) -> torch.Tensor:

        #weird sd3 controlnet specific stuff
        y = torch.zeros_like(y)

        if self.context_processor is not None:
            context = self.context_processor(context)

        hw = x.shape[-2:]
        x = self.x_embedder(x) + self.cropped_pos_embed(hw, device=x.device).to(dtype=x.dtype, device=x.device)
        x += self.pos_embed_input(hint)

        c = self.t_embedder(timesteps, dtype=x.dtype)
        if y is not None and self.y_embedder is not None:
            y = self.y_embedder(y)
            c = c + y

        if context is not None:
            context = self.context_embedder(context)

        output = []

        blocks = len(self.joint_blocks)
        for i in range(blocks):
            context, x = self.joint_blocks[i](
                context,
                x,
                c=c,
                use_checkpoint=self.use_checkpoint,
            )

            out = self.controlnet_blocks[i](x)
            count = self.depth // blocks
            if i == blocks - 1:
                count -= 1
            for j in range(count):
                output.append(out)

        return {"output": output}