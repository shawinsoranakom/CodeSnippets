def __call__(self, boxes_1, boxes_2, boxes_1_masks=None, boxes_2_masks=None):
    """Compute pairwise IOU similarity between ground truth boxes and anchors.

    B: batch_size
    N: Number of groundtruth boxes.
    M: Number of anchor boxes.

    Args:
      boxes_1: a float Tensor with M or B * M boxes.
      boxes_2: a float Tensor with N or B * N boxes, the rank must be less than
        or equal to rank of `boxes_1`.
      boxes_1_masks: a boolean Tensor with M or B * M boxes. Optional.
      boxes_2_masks: a boolean Tensor with N or B * N boxes. Optional.

    Returns:
      A Tensor with shape [M, N] or [B, M, N] representing pairwise
        iou scores, anchor per row and groundtruth_box per colulmn.

    Input shape:
      boxes_1: [N, 4], or [B, N, 4]
      boxes_2: [M, 4], or [B, M, 4]
      boxes_1_masks: [N, 1], or [B, N, 1]
      boxes_2_masks: [M, 1], or [B, M, 1]

    Output shape:
      [M, N], or [B, M, N]
    """
    boxes_1 = tf.cast(boxes_1, tf.float32)
    boxes_2 = tf.cast(boxes_2, tf.float32)

    boxes_1_rank = len(boxes_1.shape)
    boxes_2_rank = len(boxes_2.shape)
    if boxes_1_rank < 2 or boxes_1_rank > 3:
      raise ValueError(
          '`groudtruth_boxes` must be rank 2 or 3, got {}'.format(boxes_1_rank))
    if boxes_2_rank < 2 or boxes_2_rank > 3:
      raise ValueError(
          '`anchors` must be rank 2 or 3, got {}'.format(boxes_2_rank))
    if boxes_1_rank < boxes_2_rank:
      raise ValueError('`groundtruth_boxes` is unbatched while `anchors` is '
                       'batched is not a valid use case, got groundtruth_box '
                       'rank {}, and anchors rank {}'.format(
                           boxes_1_rank, boxes_2_rank))

    result = iou(boxes_1, boxes_2)
    if boxes_1_masks is None and boxes_2_masks is None:
      return result
    background_mask = None
    mask_val_t = tf.cast(self.mask_val, result.dtype) * tf.ones_like(result)
    perm = [1, 0] if boxes_2_rank == 2 else [0, 2, 1]
    if boxes_1_masks is not None and boxes_2_masks is not None:
      background_mask = tf.logical_or(boxes_1_masks,
                                      tf.transpose(boxes_2_masks, perm))
    elif boxes_1_masks is not None:
      background_mask = boxes_1_masks
    else:
      background_mask = tf.logical_or(
          tf.zeros(tf.shape(boxes_2)[:-1], dtype=tf.bool),
          tf.transpose(boxes_2_masks, perm))
    return tf.where(background_mask, mask_val_t, result)