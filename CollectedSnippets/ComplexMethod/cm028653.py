def aggregated_comparitive_iou(boxes1, boxes2=None, iou_type=0, beta=0.6):
  """Calculates the IOU between two set of boxes.

  Similar to bbox_overlap but far more versitile.

  Args:
    boxes1: a `Tensor` of shape [batch size, N, 4] representing the coordinates
      of boxes.
    boxes2: a `Tensor` of shape [batch size, N, 4] representing the coordinates
      of boxes.
    iou_type: `integer` representing the iou version to use, 0 is distance iou,
      1 is the general iou, 2 is the complete iou, any other number uses the
      standard iou.
    beta: `float` for the scaling quantity to apply to distance iou
      regularization.

  Returns:
    iou: a `Tensor` who represents the intersection over union in of the
      expected/input type.
  """
  boxes1 = tf.expand_dims(boxes1, axis=-2)

  if boxes2 is not None:
    boxes2 = tf.expand_dims(boxes2, axis=-3)
  else:
    boxes2 = tf.transpose(boxes1, perm=(0, 2, 1, 3))

  if iou_type == 0 or iou_type == 'diou':  # diou
    _, iou = compute_diou(boxes1, boxes2, beta=beta, yxyx=True)
  elif iou_type == 1 or iou_type == 'giou':  # giou
    _, iou = compute_giou(boxes1, boxes2, yxyx=True)
  elif iou_type == 2 or iou_type == 'ciou':  # ciou
    _, iou = compute_ciou(boxes1, boxes2, yxyx=True)
  else:
    iou = compute_iou(boxes1, boxes2, yxyx=True)
  return iou