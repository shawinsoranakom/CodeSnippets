def get_contrastive_denoising_training_group(
    targets,
    num_classes,
    num_queries,
    class_embed,
    num_denoising_queries=100,
    label_noise_ratio=0.5,
    box_noise_scale=1.0,
):
    """
    Creates a contrastive denoising training group using ground-truth samples. It adds noise to labels and boxes.

    Args:
        targets (`list[dict]`):
            The target objects, each containing 'class_labels' and 'boxes' for objects in an image.
        num_classes (`int`):
            Total number of classes in the dataset.
        num_queries (`int`):
            Number of query slots in the transformer.
        class_embed (`callable`):
            A function or a model layer to embed class labels.
        num_denoising_queries (`int`, *optional*, defaults to 100):
            Number of denoising queries.
        label_noise_ratio (`float`, *optional*, defaults to 0.5):
            Ratio of noise applied to labels.
        box_noise_scale (`float`, *optional*, defaults to 1.0):
            Scale of noise applied to bounding boxes.
    Returns:
        `tuple` comprising various elements:
        - **input_query_class** (`torch.FloatTensor`) --
          Class queries with applied label noise.
        - **input_query_bbox** (`torch.FloatTensor`) --
          Bounding box queries with applied box noise.
        - **attn_mask** (`torch.FloatTensor`) --
           Attention mask for separating denoising and reconstruction queries.
        - **denoising_meta_values** (`dict`) --
          Metadata including denoising positive indices, number of groups, and split sizes.
    """

    if num_denoising_queries <= 0:
        return None, None, None, None

    num_ground_truths = [len(t["class_labels"]) for t in targets]
    device = targets[0]["class_labels"].device

    max_gt_num = max(num_ground_truths)
    if max_gt_num == 0:
        return None, None, None, None

    num_groups_denoising_queries = num_denoising_queries // max_gt_num
    num_groups_denoising_queries = 1 if num_groups_denoising_queries == 0 else num_groups_denoising_queries
    # pad gt to max_num of a batch
    batch_size = len(num_ground_truths)

    input_query_class = torch.full([batch_size, max_gt_num], num_classes, dtype=torch.int32, device=device)
    input_query_bbox = torch.zeros([batch_size, max_gt_num, 4], device=device)
    pad_gt_mask = torch.zeros([batch_size, max_gt_num], dtype=torch.bool, device=device)

    for i in range(batch_size):
        num_gt = num_ground_truths[i]
        if num_gt > 0:
            input_query_class[i, :num_gt] = targets[i]["class_labels"]
            input_query_bbox[i, :num_gt] = targets[i]["boxes"]
            pad_gt_mask[i, :num_gt] = 1
    # each group has positive and negative queries.
    input_query_class = input_query_class.tile([1, 2 * num_groups_denoising_queries])
    input_query_bbox = input_query_bbox.tile([1, 2 * num_groups_denoising_queries, 1])
    pad_gt_mask = pad_gt_mask.tile([1, 2 * num_groups_denoising_queries])
    # positive and negative mask
    negative_gt_mask = torch.zeros([batch_size, max_gt_num * 2, 1], device=device)
    negative_gt_mask[:, max_gt_num:] = 1
    negative_gt_mask = negative_gt_mask.tile([1, num_groups_denoising_queries, 1])
    positive_gt_mask = 1 - negative_gt_mask
    # contrastive denoising training positive index
    positive_gt_mask = positive_gt_mask.squeeze(-1) * pad_gt_mask
    denoise_positive_idx = torch.nonzero(positive_gt_mask)[:, 1]
    denoise_positive_idx = torch.split(
        denoise_positive_idx, [n * num_groups_denoising_queries for n in num_ground_truths]
    )
    # total denoising queries
    num_denoising_queries = torch_int(max_gt_num * 2 * num_groups_denoising_queries)

    if label_noise_ratio > 0:
        mask = torch.rand_like(input_query_class, dtype=torch.float) < (label_noise_ratio * 0.5)
        # randomly put a new one here
        new_label = torch.randint_like(mask, 0, num_classes, dtype=input_query_class.dtype)
        input_query_class = torch.where(mask & pad_gt_mask, new_label, input_query_class)

    if box_noise_scale > 0:
        known_bbox = center_to_corners_format(input_query_bbox)
        diff = torch.tile(input_query_bbox[..., 2:] * 0.5, [1, 1, 2]) * box_noise_scale
        rand_sign = torch.randint_like(input_query_bbox, 0, 2) * 2.0 - 1.0
        rand_part = torch.rand_like(input_query_bbox)
        rand_part = (rand_part + 1.0) * negative_gt_mask + rand_part * (1 - negative_gt_mask)
        rand_part *= rand_sign
        known_bbox += rand_part * diff
        known_bbox.clip_(min=0.0, max=1.0)
        input_query_bbox = corners_to_center_format(known_bbox)
        input_query_bbox = inverse_sigmoid(input_query_bbox)

    input_query_class = class_embed(input_query_class)

    target_size = num_denoising_queries + num_queries
    attn_mask = torch.full([target_size, target_size], 0, dtype=torch.float, device=device)
    # match query cannot see the reconstruction
    attn_mask[num_denoising_queries:, :num_denoising_queries] = -torch.inf

    # reconstructions cannot see each other
    for i in range(num_groups_denoising_queries):
        idx_block_start = max_gt_num * 2 * i
        idx_block_end = max_gt_num * 2 * (i + 1)
        attn_mask[idx_block_start:idx_block_end, :idx_block_start] = -torch.inf
        attn_mask[idx_block_start:idx_block_end, idx_block_end:num_denoising_queries] = -torch.inf

    denoising_meta_values = {
        "dn_positive_idx": denoise_positive_idx,
        "dn_num_group": num_groups_denoising_queries,
        "dn_num_split": [num_denoising_queries, num_queries],
    }

    return input_query_class, input_query_bbox, attn_mask, denoising_meta_values