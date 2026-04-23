def _merge_image_patch_embeddings(
        self,
        image_size: torch.Tensor,
        patch_embeddings: torch.Tensor,
        *,
        image_newline=None,
        vision_aspect_ratio="anyres_max_9",
        strategy: str,
    ) -> torch.Tensor:
        if strategy == "flat":
            return patch_embeddings.flatten(0, 1)

        if strategy.startswith("spatial"):
            height = width = (
                self.config.vision_config.image_size
                // self.config.vision_config.patch_size
            )

            base_patch_embeds = patch_embeddings[0]
            if height * width != base_patch_embeds.shape[0]:
                raise ValueError(
                    "The number of patches is not consistent with the image size."
                )

            if patch_embeddings.shape[0] > 1:
                other_patch_embeds = patch_embeddings[1:]

                # Move to CPU to avoid floating-point errors
                orig_height, orig_width = image_size.tolist()

                # image_aspect_ratio == "anyres"
                num_patch_height, num_patch_width = get_anyres_image_grid_shape(
                    (orig_height, orig_width),
                    self.config.image_grid_pinpoints,
                    self.config.vision_config.image_size,
                )
                num_patches = num_patch_height * num_patch_width

                # Image patches might be padded for batch processing
                other_patch_embeds = other_patch_embeds[:num_patches].view(
                    num_patch_height, num_patch_width, height, width, -1
                )

                if "unpad" in strategy:
                    other_patch_embeds = (
                        other_patch_embeds.permute(4, 0, 2, 1, 3)
                        .contiguous()
                        .flatten(1, 2)
                        .flatten(2, 3)
                    )
                    other_patch_embeds = unpad_image(
                        other_patch_embeds, (orig_height, orig_width)
                    )
                    max_num_patches = int(
                        vision_aspect_ratio.removeprefix("anyres_max_")
                    )
                    channels, curr_height, curr_width = other_patch_embeds.shape
                    ratio = math.sqrt(
                        curr_height * curr_width / (max_num_patches * height**2)
                    )
                    if ratio > 1.1:
                        other_patch_embeds = other_patch_embeds[None]
                        other_patch_embeds = nn.functional.interpolate(
                            other_patch_embeds,
                            [int(curr_height // ratio), int(curr_width // ratio)],
                            mode="bilinear",
                        )[0]
                    if image_newline is not None:
                        other_patch_embeds = torch.cat(
                            (
                                other_patch_embeds,
                                image_newline[:, None, None]
                                .expand(*other_patch_embeds.shape[:-1], 1)
                                .to(other_patch_embeds.device),
                            ),
                            dim=-1,
                        )
                    other_patch_embeds = other_patch_embeds.flatten(1, 2).transpose(
                        0, 1
                    )
                else:
                    other_patch_embeds = (
                        other_patch_embeds.permute(0, 2, 1, 3, 4)
                        .contiguous()
                        .flatten(0, 3)
                    )

                merged_patch_embeddings = torch.cat(
                    (base_patch_embeds, other_patch_embeds), dim=0
                )
            else:
                if "unpad" in strategy:
                    merged_patch_embeddings = torch.cat(
                        (
                            base_patch_embeds,
                            self.image_newline[None].to(base_patch_embeds.device),
                        ),
                        dim=0,
                    )
                else:
                    merged_patch_embeddings = base_patch_embeds

            return merged_patch_embeddings

        raise ValueError(f"Unexpected patch merge strategy: {strategy}")