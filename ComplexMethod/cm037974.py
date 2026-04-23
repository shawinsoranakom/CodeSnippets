def _compute_num_image_tokens(
        self,
        orig_width: int,
        orig_height: int,
        dynamic_hd_size: int,
        vit_image_size: int,
        vit_patch_size: int,
        token_compression_factor: int = 2,
    ):
        """
        compute the number of tokens an image is expected to take up considering
        the image encoder architecture and exclude output features containing
        only padding pixels

        for siglip, vit_image_size=448, vit_patch_size=14, so output will be
        32x32 feature map
        NOTE right now, Phi4MM uses hard-coded token_compression_factor=2
        """
        assert vit_image_size % vit_patch_size == 0, (
            "vit_image_size must be divisible by vit_patch_size"
        )
        assert vit_image_size // vit_patch_size % token_compression_factor == 0, (
            "vit_image_size // vit_patch_size must be divisible by "
            "token_compression_factor"
        )

        target_aspect_ratio, target_height, target_width = (
            self._find_target_aspect_ratio(
                orig_width, orig_height, vit_image_size, dynamic_hd_size, min_num=1
            )
        )
        assert target_aspect_ratio[0] * vit_image_size == target_width, (
            f"{target_aspect_ratio[0]} * {vit_image_size} != {target_width}"
        )
        assert target_aspect_ratio[1] * vit_image_size == target_height, (
            f"{target_aspect_ratio[1]} * {vit_image_size} != {target_height}"
        )
        assert (
            target_height % vit_image_size == 0 and target_width % vit_image_size == 0
        )

        padding_height, padding_width = _get_padding_size(
            orig_width, orig_height, target_height, target_width
        )
        assert padding_width == 0 or padding_height == 0, (
            "padding_width or padding_height must be 0"
        )

        target_feat_width = target_width // vit_patch_size
        target_feat_height = target_height // vit_patch_size
        if padding_width >= vit_patch_size:
            assert padding_height == 0, "padding_height not 0"
            non_pad_feat_width = target_feat_width - math.floor(
                padding_width / vit_patch_size
            )
            non_pad_feat_height = target_feat_height
        elif padding_height >= vit_patch_size:
            assert padding_width == 0, "padding_width not 0"
            non_pad_feat_height = target_feat_height - math.floor(
                padding_height / vit_patch_size
            )
            non_pad_feat_width = target_feat_width
        else:
            # small padding shorter than a vit patch
            non_pad_feat_width = target_feat_width
            non_pad_feat_height = target_feat_height

        feat_width = non_pad_feat_width // token_compression_factor
        feat_height = non_pad_feat_height // token_compression_factor
        # NOTE it's possible that the non-padding feature is not divisible
        if non_pad_feat_width % token_compression_factor != 0:
            feat_width += 1
        if non_pad_feat_height % token_compression_factor != 0:
            feat_height += 1
        num_hd_patch_tokens = feat_width * feat_height
        num_hd_newline_tokens = feat_height
        vit_feature_size = vit_image_size // vit_patch_size
        num_global_image_tokens = (vit_feature_size // token_compression_factor) ** 2
        num_sep_tokens = 1
        num_global_image_newline_tokens = vit_feature_size // token_compression_factor

        return (
            num_global_image_tokens
            + num_sep_tokens
            + num_hd_patch_tokens
            + num_hd_newline_tokens
            + num_global_image_newline_tokens
        )