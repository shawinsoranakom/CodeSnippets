def _merge_semantic_and_instance_maps(
        semantic_prediction: tf.Tensor,
        instance_maps: tf.Tensor,
        thing_class_ids: tf.Tensor,
        label_divisor: int,
        stuff_area_limit: int,
        void_label: int) -> tf.Tensor:
  """Merges semantic and instance maps to obtain panoptic segmentation.

  This function merges the semantic segmentation and class-agnostic
  instance segmentation to form the panoptic segmentation. In particular,
  the class label of each instance mask is inferred from the majority
  votes from the corresponding pixels in the semantic segmentation. This
  operation is first proposed in the DeeperLab paper and adopted by the
  Panoptic-DeepLab.
  - DeeperLab: Single-Shot Image Parser, T-J Yang, et al. arXiv:1902.05093.
  - Panoptic-DeepLab, B. Cheng, et al. In CVPR, 2020.
  Note that this function only supports batch = 1 for simplicity. Additionally,
  this function has a slightly different implementation from the provided
  TensorFlow implementation `merge_ops` but with a similar performance. This
  function is mainly used as a backup solution when you could not successfully
  compile the provided TensorFlow implementation. To reproduce our results,
  please use the provided TensorFlow implementation (i.e., not use this
  function, but the `merge_ops.merge_semantic_and_instance_maps`).

  Args:
    semantic_prediction: A tf.Tensor of shape [batch, height, width].
    instance_maps: A tf.Tensor of shape [batch, height, width].
    thing_class_ids: A tf.Tensor of shape [N] containing N thing indices.
    label_divisor: An integer specifying the label divisor of the dataset.
    stuff_area_limit: An integer specifying the number of pixels that stuff
      regions need to have at least. The stuff region will be included in the
      panoptic prediction, only if its area is larger than the limit; otherwise,
      it will be re-assigned as void_label.
    void_label: An integer specifying the void label.
  Returns:
    panoptic_prediction: A tf.Tensor with shape [batch, height, width].
  """
  prediction_shape = semantic_prediction.get_shape().as_list()
  # This implementation only supports batch size of 1. Since model construction
  # might lose batch size information (and leave it to None), override it here.
  prediction_shape[0] = 1
  semantic_prediction = tf.ensure_shape(semantic_prediction, prediction_shape)
  instance_maps = tf.ensure_shape(instance_maps, prediction_shape)

  # Default panoptic_prediction to have semantic label = void_label.
  panoptic_prediction = tf.ones_like(
      semantic_prediction) * void_label * label_divisor

  # Start to paste predicted `thing` regions to panoptic_prediction.
  # Infer `thing` segmentation regions from semantic prediction.
  semantic_thing_segmentation = tf.zeros_like(semantic_prediction,
                                              dtype=tf.bool)
  for thing_class in thing_class_ids:
    semantic_thing_segmentation = tf.math.logical_or(
        semantic_thing_segmentation,
        semantic_prediction == thing_class)
  # Keep track of how many instances for each semantic label.
  num_instance_per_semantic_label = tf.TensorArray(
      tf.int32, size=0, dynamic_size=True, clear_after_read=False)
  instance_ids, _ = tf.unique(tf.reshape(instance_maps, [-1]))
  for instance_id in instance_ids:
    # Instance ID 0 is reserved for crowd region.
    if instance_id == 0:
      continue
    thing_mask = tf.math.logical_and(instance_maps == instance_id,
                                     semantic_thing_segmentation)
    if tf.reduce_sum(tf.cast(thing_mask, tf.int32)) == 0:
      continue
    semantic_bin_counts = tf.math.bincount(
        tf.boolean_mask(semantic_prediction, thing_mask))
    semantic_majority = tf.cast(
        tf.math.argmax(semantic_bin_counts), tf.int32)

    while num_instance_per_semantic_label.size() <= semantic_majority:
      num_instance_per_semantic_label = num_instance_per_semantic_label.write(
          num_instance_per_semantic_label.size(), 0)

    new_instance_id = (
        num_instance_per_semantic_label.read(semantic_majority) + 1)
    num_instance_per_semantic_label = num_instance_per_semantic_label.write(
        semantic_majority, new_instance_id)
    panoptic_prediction = tf.where(
        thing_mask,
        tf.ones_like(panoptic_prediction) * semantic_majority * label_divisor
        + new_instance_id,
        panoptic_prediction)

  # Done with `num_instance_per_semantic_label` tensor array.
  num_instance_per_semantic_label.close()

  # Start to paste predicted `stuff` regions to panoptic prediction.
  instance_stuff_regions = instance_maps == 0
  semantic_ids, _ = tf.unique(tf.reshape(semantic_prediction, [-1]))
  for semantic_id in semantic_ids:
    if tf.reduce_sum(tf.cast(thing_class_ids == semantic_id, tf.int32)) > 0:
      continue
    # Check stuff area.
    stuff_mask = tf.math.logical_and(semantic_prediction == semantic_id,
                                     instance_stuff_regions)
    stuff_area = tf.reduce_sum(tf.cast(stuff_mask, tf.int32))
    if stuff_area >= stuff_area_limit:
      panoptic_prediction = tf.where(
          stuff_mask,
          tf.ones_like(panoptic_prediction) * semantic_id * label_divisor,
          panoptic_prediction)

  return panoptic_prediction