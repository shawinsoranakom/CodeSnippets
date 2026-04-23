def get_cdn_group(
    batch: dict[str, Any],
    num_classes: int,
    num_queries: int,
    class_embed: torch.Tensor,
    num_dn: int = 100,
    cls_noise_ratio: float = 0.5,
    box_noise_scale: float = 1.0,
    training: bool = False,
) -> tuple[torch.Tensor | None, torch.Tensor | None, torch.Tensor | None, dict[str, Any] | None]:
    """Generate contrastive denoising training group with positive and negative samples from ground truths.

    This function creates denoising queries for contrastive denoising training by adding noise to ground truth bounding
    boxes and class labels. It generates both positive and negative samples to improve model robustness.

    Args:
        batch (dict[str, Any]): Batch dictionary containing 'cls' (torch.Tensor with shape (num_gts,)), 'bboxes'
            (torch.Tensor with shape (num_gts, 4)), 'batch_idx' (torch.Tensor), and 'gt_groups' (list[int]) indicating
            number of ground truths per image.
        num_classes (int): Total number of object classes.
        num_queries (int): Number of object queries.
        class_embed (torch.Tensor): Class embedding weights to map labels to embedding space.
        num_dn (int): Number of denoising queries to generate.
        cls_noise_ratio (float): Noise ratio for class labels.
        box_noise_scale (float): Noise scale for bounding box coordinates.
        training (bool): Whether model is in training mode.

    Returns:
        padding_cls (torch.Tensor | None): Modified class embeddings for denoising with shape (bs, num_dn, embed_dim).
        padding_bbox (torch.Tensor | None): Modified bounding boxes for denoising with shape (bs, num_dn, 4).
        attn_mask (torch.Tensor | None): Attention mask for denoising with shape (tgt_size, tgt_size).
        dn_meta (dict[str, Any] | None): Meta information dictionary containing denoising parameters.

    Examples:
        Generate denoising group for training
        >>> batch = {
        ...     "cls": torch.tensor([0, 1, 2]),
        ...     "bboxes": torch.rand(3, 4),
        ...     "batch_idx": torch.tensor([0, 0, 1]),
        ...     "gt_groups": [2, 1],
        ... }
        >>> class_embed = torch.rand(80, 256)  # 80 classes, 256 embedding dim
        >>> cdn_outputs = get_cdn_group(batch, 80, 100, class_embed, training=True)
    """
    if (not training) or num_dn <= 0 or batch is None:
        return None, None, None, None
    gt_groups = batch["gt_groups"]
    total_num = sum(gt_groups)
    max_nums = max(gt_groups)
    if max_nums == 0:
        return None, None, None, None

    num_group = num_dn // max_nums
    num_group = 1 if num_group == 0 else num_group
    # Pad gt to max_num of a batch
    bs = len(gt_groups)
    gt_cls = batch["cls"]  # (bs*num, )
    gt_bbox = batch["bboxes"]  # bs*num, 4
    b_idx = batch["batch_idx"]

    # Each group has positive and negative queries
    dn_cls = gt_cls.repeat(2 * num_group)  # (2*num_group*bs*num, )
    dn_bbox = gt_bbox.repeat(2 * num_group, 1)  # 2*num_group*bs*num, 4
    dn_b_idx = b_idx.repeat(2 * num_group).view(-1)  # (2*num_group*bs*num, )

    # Positive and negative mask
    # (bs*num*num_group, ), the second total_num*num_group part as negative samples
    neg_idx = torch.arange(total_num * num_group, dtype=torch.long, device=gt_bbox.device) + num_group * total_num

    if cls_noise_ratio > 0:
        # Apply class label noise to half of the samples
        mask = torch.rand(dn_cls.shape) < (cls_noise_ratio * 0.5)
        idx = torch.nonzero(mask).squeeze(-1)
        # Randomly assign new class labels
        new_label = torch.randint_like(idx, 0, num_classes, dtype=dn_cls.dtype, device=dn_cls.device)
        dn_cls[idx] = new_label

    if box_noise_scale > 0:
        known_bbox = xywh2xyxy(dn_bbox)

        diff = (dn_bbox[..., 2:] * 0.5).repeat(1, 2) * box_noise_scale  # 2*num_group*bs*num, 4

        rand_sign = torch.randint_like(dn_bbox, 0, 2) * 2.0 - 1.0
        rand_part = torch.rand_like(dn_bbox)
        rand_part[neg_idx] += 1.0
        rand_part *= rand_sign
        known_bbox += rand_part * diff
        known_bbox.clip_(min=0.0, max=1.0)
        dn_bbox = xyxy2xywh(known_bbox)
        dn_bbox = torch.logit(dn_bbox, eps=1e-6)  # inverse sigmoid

    num_dn = int(max_nums * 2 * num_group)  # total denoising queries
    dn_cls_embed = class_embed[dn_cls]  # bs*num * 2 * num_group, 256
    padding_cls = torch.zeros(bs, num_dn, dn_cls_embed.shape[-1], device=gt_cls.device)
    padding_bbox = torch.zeros(bs, num_dn, 4, device=gt_bbox.device)

    map_indices = torch.cat([torch.tensor(range(num), dtype=torch.long) for num in gt_groups])
    pos_idx = torch.stack([map_indices + max_nums * i for i in range(num_group)], dim=0)

    map_indices = torch.cat([map_indices + max_nums * i for i in range(2 * num_group)])
    padding_cls[(dn_b_idx, map_indices)] = dn_cls_embed
    padding_bbox[(dn_b_idx, map_indices)] = dn_bbox

    tgt_size = num_dn + num_queries
    attn_mask = torch.zeros([tgt_size, tgt_size], dtype=torch.bool)
    # Match query cannot see the reconstruct
    attn_mask[num_dn:, :num_dn] = True
    # Reconstruct cannot see each other
    for i in range(num_group):
        if i == 0:
            attn_mask[max_nums * 2 * i : max_nums * 2 * (i + 1), max_nums * 2 * (i + 1) : num_dn] = True
        if i == num_group - 1:
            attn_mask[max_nums * 2 * i : max_nums * 2 * (i + 1), : max_nums * i * 2] = True
        else:
            attn_mask[max_nums * 2 * i : max_nums * 2 * (i + 1), max_nums * 2 * (i + 1) : num_dn] = True
            attn_mask[max_nums * 2 * i : max_nums * 2 * (i + 1), : max_nums * 2 * i] = True
    dn_meta = {
        "dn_pos_idx": [p.reshape(-1) for p in pos_idx.cpu().split(list(gt_groups), dim=1)],
        "dn_num_group": num_group,
        "dn_num_split": [num_dn, num_queries],
    }

    return (
        padding_cls.to(class_embed.device),
        padding_bbox.to(class_embed.device),
        attn_mask.to(class_embed.device),
        dn_meta,
    )