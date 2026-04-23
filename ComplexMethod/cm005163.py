def merge_patches(patches: torch.Tensor, batch_size: int, padding: int) -> torch.Tensor:
    """Merges smaller patches into image-like feature map."""
    n_patches, hidden_size, out_size, out_size = patches.shape
    n_patches_per_batch = n_patches // batch_size
    sqrt_n_patches_per_batch = torch_int(n_patches_per_batch**0.5)
    new_out_size = sqrt_n_patches_per_batch * out_size

    if n_patches == batch_size:
        # merge only if the patches were created from scaled image
        # patches are not created when scaled image size is equal to patch size
        return patches

    if n_patches_per_batch < 4:
        # for each batch, at least 4 small patches are required to
        # recreate a large square patch from merging them and later padding is applied
        # 3 x (8x8) patches becomes 1 x ( 8x8 ) patch (extra patch ignored, no padding)
        # 4 x (8x8) patches becomes 1 x (16x16) patch (padding later)
        # 5 x (8x8) patches becomes 1 x (16x16) patch (extra patch ignored, padding later)
        # 9 x (8x8) patches becomes 1 x (24x24) patch (padding later)
        # thus the following code only rearranges the patches and removes extra ones
        padding = 0

    # make sure padding is not large enough to remove more than half of the patch
    padding = min(out_size // 4, padding)

    if padding == 0:
        # faster when no padding is required
        merged = patches.reshape(n_patches_per_batch, batch_size, hidden_size, out_size, out_size)
        merged = merged.permute(1, 2, 0, 3, 4)
        merged = merged[:, :, : sqrt_n_patches_per_batch**2, :, :]
        merged = merged.reshape(
            batch_size, hidden_size, sqrt_n_patches_per_batch, sqrt_n_patches_per_batch, out_size, out_size
        )
        merged = merged.permute(0, 1, 2, 4, 3, 5)
        merged = merged.reshape(batch_size, hidden_size, new_out_size, new_out_size)
    else:
        # padding example:
        # let out_size = 8, new_out_size = 32, padding = 2
        # each patch is separated by "|"
        # and padding is applied to the merging edges of each patch
        # 00 01 02 03 04 05 06 07 | 08 09 10 11 12 13 14 15 | 16 17 18 19 20 21 22 23 | 24 25 26 27 28 29 30 31
        # 00 01 02 03 04 05 -- -- | -- -- 10 11 12 13 -- -- | -- -- 18 19 20 21 -- -- | -- -- 26 27 28 29 30 31
        i = 0
        boxes = []
        for h in range(sqrt_n_patches_per_batch):
            boxes_in_row = []
            for w in range(sqrt_n_patches_per_batch):
                box = patches[batch_size * i : batch_size * (i + 1)]

                # collect paddings
                paddings = [0, 0, 0, 0]
                if h != 0:
                    # remove pad from height if box is not at top border
                    paddings[0] = padding
                if w != 0:
                    # remove pad from width if box is not at left border
                    paddings[2] = padding
                if h != sqrt_n_patches_per_batch - 1:
                    # remove pad from height if box is not at bottom border
                    paddings[1] = padding
                if w != sqrt_n_patches_per_batch - 1:
                    # remove pad from width if box is not at right border
                    paddings[3] = padding

                # remove paddings
                _, _, box_h, box_w = box.shape
                pad_top, pad_bottom, pad_left, pad_right = paddings
                box = box[:, :, pad_top : box_h - pad_bottom, pad_left : box_w - pad_right]

                boxes_in_row.append(box)
                i += 1
            boxes_in_row = torch.cat(boxes_in_row, dim=-1)
            boxes.append(boxes_in_row)
        merged = torch.cat(boxes, dim=-2)

    return merged