def batch_assign_confidences(target_assigner,
                             anchors_batch,
                             gt_box_batch,
                             gt_class_confidences_batch,
                             gt_weights_batch=None,
                             unmatched_class_label=None,
                             include_background_class=True,
                             implicit_class_weight=1.0):
  """Batched assignment of classification and regression targets.

  This differences between batch_assign_confidences and batch_assign_targets:
   - 'batch_assign_targets' supports scalar (agnostic), vector (multiclass) and
     tensor (high-dimensional) targets. 'batch_assign_confidences' only support
     scalar (agnostic) and vector (multiclass) targets.
   - 'batch_assign_targets' assumes the input class tensor using the binary
     one/K-hot encoding. 'batch_assign_confidences' takes the class confidence
     scores as the input, where 1 means positive classes, 0 means implicit
     negative classes, and -1 means explicit negative classes.
   - 'batch_assign_confidences' assigns the targets in the similar way as
     'batch_assign_targets' except that it gives different weights for implicit
     and explicit classes. This allows user to control the negative gradients
     pushed differently for implicit and explicit examples during the training.

  Args:
    target_assigner: a target assigner.
    anchors_batch: BoxList representing N box anchors or list of BoxList objects
      with length batch_size representing anchor sets.
    gt_box_batch: a list of BoxList objects with length batch_size
      representing groundtruth boxes for each image in the batch
    gt_class_confidences_batch: a list of tensors with length batch_size, where
      each tensor has shape [num_gt_boxes_i, classification_target_size] and
      num_gt_boxes_i is the number of boxes in the ith boxlist of
      gt_box_batch. Note that in this tensor, 1 means explicit positive class,
      -1 means explicit negative class, and 0 means implicit negative class.
    gt_weights_batch: A list of 1-D tf.float32 tensors of shape
      [num_gt_boxes_i] containing weights for groundtruth boxes.
    unmatched_class_label: a float32 tensor with shape [d_1, d_2, ..., d_k]
      which is consistent with the classification target for each
      anchor (and can be empty for scalar targets).  This shape must thus be
      compatible with the groundtruth labels that are passed to the "assign"
      function (which have shape [num_gt_boxes, d_1, d_2, ..., d_k]).
    include_background_class: whether or not gt_class_confidences_batch includes
      the background class.
    implicit_class_weight: the weight assigned to implicit examples.

  Returns:
    batch_cls_targets: a tensor with shape [batch_size, num_anchors,
      num_classes],
    batch_cls_weights: a tensor with shape [batch_size, num_anchors,
      num_classes],
    batch_reg_targets: a tensor with shape [batch_size, num_anchors,
      box_code_dimension]
    batch_reg_weights: a tensor with shape [batch_size, num_anchors],
    match: an int32 tensor of shape [batch_size, num_anchors] containing result
      of anchor groundtruth matching. Each position in the tensor indicates an
      anchor and holds the following meaning:
      (1) if match[x, i] >= 0, anchor i is matched with groundtruth match[x, i].
      (2) if match[x, i]=-1, anchor i is marked to be background .
      (3) if match[x, i]=-2, anchor i is ignored since it is not background and
          does not have sufficient overlap to call it a foreground.

  Raises:
    ValueError: if input list lengths are inconsistent, i.e.,
      batch_size == len(gt_box_batch) == len(gt_class_targets_batch)
      and batch_size == len(anchors_batch) unless anchors_batch is a single
      BoxList, or if any element in gt_class_confidences_batch has rank > 2.
  """
  if not isinstance(anchors_batch, list):
    anchors_batch = len(gt_box_batch) * [anchors_batch]
  if not all(
      isinstance(anchors, box_list.BoxList) for anchors in anchors_batch):
    raise ValueError('anchors_batch must be a BoxList or list of BoxLists.')
  if not (len(anchors_batch)
          == len(gt_box_batch)
          == len(gt_class_confidences_batch)):
    raise ValueError('batch size incompatible with lengths of anchors_batch, '
                     'gt_box_batch and gt_class_confidences_batch.')

  cls_targets_list = []
  cls_weights_list = []
  reg_targets_list = []
  reg_weights_list = []
  match_list = []
  if gt_weights_batch is None:
    gt_weights_batch = [None] * len(gt_class_confidences_batch)
  for anchors, gt_boxes, gt_class_confidences, gt_weights in zip(
      anchors_batch, gt_box_batch, gt_class_confidences_batch,
      gt_weights_batch):

    if (gt_class_confidences is not None and
        len(gt_class_confidences.get_shape().as_list()) > 2):
      raise ValueError('The shape of the class target is not supported. ',
                       gt_class_confidences.get_shape())

    cls_targets, _, reg_targets, _, match = target_assigner.assign(
        anchors, gt_boxes, gt_class_confidences, unmatched_class_label,
        groundtruth_weights=gt_weights)

    if include_background_class:
      cls_targets_without_background = tf.slice(
          cls_targets, [0, 1], [-1, -1])
    else:
      cls_targets_without_background = cls_targets

    positive_mask = tf.greater(cls_targets_without_background, 0.0)
    negative_mask = tf.less(cls_targets_without_background, 0.0)
    explicit_example_mask = tf.logical_or(positive_mask, negative_mask)
    positive_anchors = tf.reduce_any(positive_mask, axis=-1)

    regression_weights = tf.cast(positive_anchors, dtype=tf.float32)
    regression_targets = (
        reg_targets * tf.expand_dims(regression_weights, axis=-1))
    regression_weights_expanded = tf.expand_dims(regression_weights, axis=-1)

    cls_targets_without_background = (
        cls_targets_without_background *
        (1 - tf.cast(negative_mask, dtype=tf.float32)))
    cls_weights_without_background = ((1 - implicit_class_weight) * tf.cast(
        explicit_example_mask, dtype=tf.float32) + implicit_class_weight)

    if include_background_class:
      cls_weights_background = (
          (1 - implicit_class_weight) * regression_weights_expanded
          + implicit_class_weight)
      classification_weights = tf.concat(
          [cls_weights_background, cls_weights_without_background], axis=-1)
      cls_targets_background = 1 - regression_weights_expanded
      classification_targets = tf.concat(
          [cls_targets_background, cls_targets_without_background], axis=-1)
    else:
      classification_targets = cls_targets_without_background
      classification_weights = cls_weights_without_background

    cls_targets_list.append(classification_targets)
    cls_weights_list.append(classification_weights)
    reg_targets_list.append(regression_targets)
    reg_weights_list.append(regression_weights)
    match_list.append(match)
  batch_cls_targets = tf.stack(cls_targets_list)
  batch_cls_weights = tf.stack(cls_weights_list)
  batch_reg_targets = tf.stack(reg_targets_list)
  batch_reg_weights = tf.stack(reg_weights_list)
  batch_match = tf.stack(match_list)
  return (batch_cls_targets, batch_cls_weights, batch_reg_targets,
          batch_reg_weights, batch_match)