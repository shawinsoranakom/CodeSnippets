def forward(
        self, embeddings, lengths, image_shapes, h_coords, w_coords
    ) -> torch.Tensor:
        pos_embed_weight = self.position_embedding.weight
        hidden_size = pos_embed_weight.shape[1]
        total_seq = h_coords.shape[0]
        device = pos_embed_weight.device

        # Move coordinates to correct device
        h_coords, w_coords = h_coords.to(device), w_coords.to(device)

        # Handle empty sequence case
        if total_seq == 0:
            adapted_pos_embed = torch.empty(
                0, hidden_size, device=device, dtype=pos_embed_weight.dtype
            )
        else:
            # Convert inputs to tensors if needed
            if isinstance(lengths, list):
                lengths = torch.tensor(lengths, device=device, dtype=torch.long)
            if not isinstance(image_shapes, torch.Tensor):
                image_shapes = torch.tensor(
                    image_shapes, device=device, dtype=torch.long
                )

            # Prepare 2D position embedding
            orig_size_sq = pos_embed_weight.shape[0]
            orig_size = int(orig_size_sq**0.5)
            pos_embed_2d = (
                pos_embed_weight.view(orig_size, orig_size, hidden_size)
                .permute(2, 0, 1)
                .unsqueeze(0)
                .to(device=device, dtype=torch.float32)
            )

            # Calculate target dimensions for each patch
            # Add bounds checking for data parallel mode
            if len(lengths) > image_shapes.shape[0]:
                # In data parallel mode, some GPUs might not have all
                # image shapes
                # Use available image shapes, cycling if necessary
                target_h_list = []
                target_w_list = []
                for i in range(len(lengths)):
                    # Cycle through available shapes
                    shape_idx = i % image_shapes.shape[0]
                    target_h_list.append(image_shapes[shape_idx, 1].repeat(lengths[i]))
                    target_w_list.append(image_shapes[shape_idx, 2].repeat(lengths[i]))
                target_h = torch.cat(target_h_list).to(
                    device=device, dtype=torch.float32
                )
                target_w = torch.cat(target_w_list).to(
                    device=device, dtype=torch.float32
                )
            else:
                target_h = torch.cat(
                    [image_shapes[i, 1].repeat(lengths[i]) for i in range(len(lengths))]
                ).to(device=device, dtype=torch.float32)
                target_w = torch.cat(
                    [image_shapes[i, 2].repeat(lengths[i]) for i in range(len(lengths))]
                ).to(device=device, dtype=torch.float32)

            # Normalize coordinates to [-1, 1] range for grid_sample
            h_coords = h_coords.to(device=device, dtype=torch.float32)
            w_coords = w_coords.to(device=device, dtype=torch.float32)
            norm_w = ((w_coords + 0.5) / target_w) * 2 - 1
            norm_h = ((h_coords + 0.5) / target_h) * 2 - 1

            # Create sampling grid
            grid = torch.stack((norm_w, norm_h), dim=-1).unsqueeze(0).unsqueeze(2)

            # Perform bicubic interpolation
            interpolated_embed_fp32 = F.grid_sample(
                pos_embed_2d,
                grid,
                mode="bicubic",
                align_corners=False,
                padding_mode="border",
            )

            # Reshape and convert back to original dtype
            adapted_pos_embed_fp32 = (
                interpolated_embed_fp32.squeeze(0).squeeze(-1).permute(1, 0)
            )
            adapted_pos_embed = adapted_pos_embed_fp32.to(pos_embed_weight.dtype).to(
                embeddings.device
            )

        # Add adapted position encoding to embeddings
        embeddings = embeddings + adapted_pos_embed
        return embeddings