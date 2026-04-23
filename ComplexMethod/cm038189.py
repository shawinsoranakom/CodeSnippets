def image_pixels_to_features(
        self,
        pixel_values: torch.FloatTensor,
        spatial_shapes: torch.Tensor,
    ) -> torch.Tensor:
        assert spatial_shapes.device.type == "cpu", (
            "Expected `spatial_shapes` on CPU to avoid device-to-host sync in "
            "variable-length packing."
        )

        pixel_values = pixel_values.to(
            dtype=self.vision_tower.vision_model.embeddings.patch_embedding.weight.dtype
        )  # fp16 compatibility

        # LFM2-VL's HF processor pads patch sequences with trailing zeros.
        # Pack patch tokens upfront so the vision tower runs entirely unpadded.
        spatial_shapes_list: list[list[int]] = spatial_shapes.tolist()
        lengths_list = [h * w for h, w in spatial_shapes_list]
        total_tokens = int(sum(lengths_list))
        lengths_cpu = (spatial_shapes[:, 0] * spatial_shapes[:, 1]).to(
            dtype=torch.int32
        )
        max_seqlen = (
            lengths_cpu.max().reshape(1)
            if lengths_cpu.numel()
            else torch.tensor([0], dtype=torch.int32)
        )

        if total_tokens == 0:
            return []

        packed_pixel_values = pixel_values.new_empty(
            (total_tokens, pixel_values.shape[-1])
        )
        offset = 0
        for i, length in enumerate(lengths_list):
            if length <= 0:
                continue
            packed_pixel_values[offset : offset + length].copy_(
                pixel_values[i, :length]
            )
            offset += length
        packed_pixel_values = packed_pixel_values.unsqueeze(0)

        lengths = torch.tensor(
            lengths_list, dtype=torch.int32, device=pixel_values.device
        )
        cu_seqlens = torch.zeros(
            lengths.shape[0] + 1,
            dtype=torch.int32,
            device=pixel_values.device,
        )
        cu_seqlens[1:] = torch.cumsum(lengths, dim=0)

        with set_forward_context(None, self.vllm_config):
            vision_outputs = self.vision_tower(
                pixel_values_packed=packed_pixel_values,
                spatial_shapes=spatial_shapes,
                cu_seqlens=cu_seqlens,
                max_seqlen=max_seqlen,
            )
        image_outputs_packed = getattr(
            vision_outputs, "last_hidden_state", vision_outputs
        )
        vision_features_packed = image_outputs_packed[0]

        factor = self.multi_modal_projector.factor
        projected_lengths_list: list[int] = []
        for (height, width), length in zip(spatial_shapes_list, lengths_list):
            if length <= 0:
                projected_lengths_list.append(0)
                continue
            if height % factor != 0 or width % factor != 0:
                raise ValueError(
                    "spatial_shapes must be divisible by downsample_factor: "
                    f"got ({height}, {width}) with factor={factor}."
                )
            projected_lengths_list.append((height // factor) * (width // factor))

        projected_packed = self.multi_modal_projector(
            vision_features_packed=vision_features_packed,
            spatial_shapes=spatial_shapes,
        )

        image_features: list[torch.Tensor] = []
        offset = 0
        for out_len in projected_lengths_list:
            image_features.append(projected_packed[offset : offset + out_len])
            offset += out_len

        return image_features