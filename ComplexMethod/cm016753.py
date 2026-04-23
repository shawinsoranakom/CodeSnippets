def forward_before_blocks(
        self,
        x: torch.Tensor,
        timesteps: torch.Tensor,
        crossattn_emb: torch.Tensor,
        crossattn_mask: Optional[torch.Tensor] = None,
        fps: Optional[torch.Tensor] = None,
        image_size: Optional[torch.Tensor] = None,
        padding_mask: Optional[torch.Tensor] = None,
        scalar_feature: Optional[torch.Tensor] = None,
        data_type: Optional[DataType] = DataType.VIDEO,
        latent_condition: Optional[torch.Tensor] = None,
        latent_condition_sigma: Optional[torch.Tensor] = None,
        **kwargs,
    ) -> torch.Tensor:
        """
        Args:
            x: (B, C, T, H, W) tensor of spatial-temp inputs
            timesteps: (B, ) tensor of timesteps
            crossattn_emb: (B, N, D) tensor of cross-attention embeddings
            crossattn_mask: (B, N) tensor of cross-attention masks
        """
        del kwargs
        assert isinstance(
            data_type, DataType
        ), f"Expected DataType, got {type(data_type)}. We need discuss this flag later."
        original_shape = x.shape
        x_B_T_H_W_D, rope_emb_L_1_1_D, extra_pos_emb_B_T_H_W_D_or_T_H_W_B_D = self.prepare_embedded_sequence(
            x,
            fps=fps,
            padding_mask=padding_mask,
            latent_condition=latent_condition,
            latent_condition_sigma=latent_condition_sigma,
        )
        # logging affline scale information
        affline_scale_log_info = {}

        timesteps_B_D, adaln_lora_B_3D = self.t_embedder[1](self.t_embedder[0](timesteps.flatten()).to(x.dtype))
        affline_emb_B_D = timesteps_B_D
        affline_scale_log_info["timesteps_B_D"] = timesteps_B_D.detach()

        if scalar_feature is not None:
            raise NotImplementedError("Scalar feature is not implemented yet.")

        affline_scale_log_info["affline_emb_B_D"] = affline_emb_B_D.detach()
        affline_emb_B_D = self.affline_norm(affline_emb_B_D)

        if self.use_cross_attn_mask:
            if crossattn_mask is not None and not torch.is_floating_point(crossattn_mask):
                crossattn_mask = (crossattn_mask - 1).to(x.dtype) * torch.finfo(x.dtype).max
            crossattn_mask = crossattn_mask[:, None, None, :]  # .to(dtype=torch.bool)  # [B, 1, 1, length]
        else:
            crossattn_mask = None

        if self.blocks["block0"].x_format == "THWBD":
            x = rearrange(x_B_T_H_W_D, "B T H W D -> T H W B D")
            if extra_pos_emb_B_T_H_W_D_or_T_H_W_B_D is not None:
                extra_pos_emb_B_T_H_W_D_or_T_H_W_B_D = rearrange(
                    extra_pos_emb_B_T_H_W_D_or_T_H_W_B_D, "B T H W D -> T H W B D"
                )
            crossattn_emb = rearrange(crossattn_emb, "B M D -> M B D")

            if crossattn_mask:
                crossattn_mask = rearrange(crossattn_mask, "B M -> M B")

        elif self.blocks["block0"].x_format == "BTHWD":
            x = x_B_T_H_W_D
        else:
            raise ValueError(f"Unknown x_format {self.blocks[0].x_format}")
        output = {
            "x": x,
            "affline_emb_B_D": affline_emb_B_D,
            "crossattn_emb": crossattn_emb,
            "crossattn_mask": crossattn_mask,
            "rope_emb_L_1_1_D": rope_emb_L_1_1_D,
            "adaln_lora_B_3D": adaln_lora_B_3D,
            "original_shape": original_shape,
            "extra_pos_emb_B_T_H_W_D_or_T_H_W_B_D": extra_pos_emb_B_T_H_W_D_or_T_H_W_B_D,
        }
        return output