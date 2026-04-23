def forward(self, x: torch.Tensor) -> list[torch.Tensor]:
        """Vit forward path and get feature maps."""
        x = self.patch_embed(x)
        h, w = x.shape[1], x.shape[2]

        s = 0
        if self.retain_cls_token:
            # If cls_token is retained, we don't
            # maintain spatial shape
            x = torch.cat([self.class_embedding, x.flatten(1, 2)], dim=1)
            s = 1

        if self.pos_embed is not None:
            x = x + get_abs_pos(
                self.pos_embed,
                self.pretrain_use_cls_token,
                (h, w),
                self.retain_cls_token,
                tiling=self.tile_abs_pos,
            )

        x = self.ln_pre(x)

        outputs = []
        for i, blk in enumerate(self.blocks):
            if self.use_act_checkpoint and self.training:
                x = checkpoint.checkpoint(blk, x, use_reentrant=False)
            else:
                x = blk(x)
            if (i == self.full_attn_ids[-1]) or (self.return_interm_layers and i in self.full_attn_ids):
                if i == self.full_attn_ids[-1]:
                    x = self.ln_post(x)

                feats = x[:, s:]
                if feats.ndim == 4:
                    feats = feats.permute(0, 3, 1, 2)
                else:
                    assert feats.ndim == 3
                    h = w = math.sqrt(feats.shape[1])
                    feats = feats.reshape(feats.shape[0], h, w, feats.shape[-1]).permute(0, 3, 1, 2)

                outputs.append(feats)

        return outputs