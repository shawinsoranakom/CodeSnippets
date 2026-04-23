def _format_groundtruth_data(self, image_shapes):
    """Helper function for preparing groundtruth data for target assignment.

    In order to be consistent with the model.DetectionModel interface,
    groundtruth boxes are specified in normalized coordinates and classes are
    specified as label indices with no assumed background category.  To prepare
    for target assignment, we:
    1) convert boxes to absolute coordinates,
    2) add a background class at class index 0
    3) groundtruth instance masks, if available, are resized to match
       image_shape.

    Args:
      image_shapes: a 2-D int32 tensor of shape [batch_size, 3] containing
        shapes of input image in the batch.

    Returns:
      groundtruth_boxlists: A list of BoxLists containing (absolute) coordinates
        of the groundtruth boxes.
      groundtruth_classes_with_background_list: A list of 2-D one-hot
        (or k-hot) tensors of shape [num_boxes, num_classes+1] containing the
        class targets with the 0th index assumed to map to the background class.
      groundtruth_masks_list: If present, a list of 3-D tf.float32 tensors of
        shape [num_boxes, image_height, image_width] containing instance masks.
        This is set to None if no masks exist in the provided groundtruth.
    """
    # pylint: disable=g-complex-comprehension
    groundtruth_boxlists = [
        box_list_ops.to_absolute_coordinates(
            box_list.BoxList(boxes), image_shapes[i, 0], image_shapes[i, 1])
        for i, boxes in enumerate(
            self.groundtruth_lists(fields.BoxListFields.boxes))
    ]
    groundtruth_classes_with_background_list = []
    for one_hot_encoding in self.groundtruth_lists(
        fields.BoxListFields.classes):
      groundtruth_classes_with_background_list.append(
          tf.cast(
              tf.pad(one_hot_encoding, [[0, 0], [1, 0]], mode='CONSTANT'),
              dtype=tf.float32))

    groundtruth_masks_list = self._groundtruth_lists.get(
        fields.BoxListFields.masks)
    # TODO(rathodv): Remove mask resizing once the legacy pipeline is deleted.
    if groundtruth_masks_list is not None and self._resize_masks:
      resized_masks_list = []
      for mask in groundtruth_masks_list:

        _, resized_mask, _ = self._image_resizer_fn(
            # Reuse the given `image_resizer_fn` to resize groundtruth masks.
            # `mask` tensor for an image is of the shape [num_masks,
            # image_height, image_width]. Below we create a dummy image of the
            # the shape [image_height, image_width, 1] to use with
            # `image_resizer_fn`.
            image=tf.zeros(tf.stack([tf.shape(mask)[1],
                                     tf.shape(mask)[2], 1])),
            masks=mask)
        resized_masks_list.append(resized_mask)

      groundtruth_masks_list = resized_masks_list
    # Masks could be set to bfloat16 in the input pipeline for performance
    # reasons. Convert masks back to floating point space here since the rest of
    # this module assumes groundtruth to be of float32 type.
    float_groundtruth_masks_list = []
    if groundtruth_masks_list:
      for mask in groundtruth_masks_list:
        float_groundtruth_masks_list.append(tf.cast(mask, tf.float32))
      groundtruth_masks_list = float_groundtruth_masks_list

    if self.groundtruth_has_field(fields.BoxListFields.weights):
      groundtruth_weights_list = self.groundtruth_lists(
          fields.BoxListFields.weights)
    else:
      # Set weights for all batch elements equally to 1.0
      groundtruth_weights_list = []
      for groundtruth_classes in groundtruth_classes_with_background_list:
        num_gt = tf.shape(groundtruth_classes)[0]
        groundtruth_weights = tf.ones(num_gt)
        groundtruth_weights_list.append(groundtruth_weights)

    return (groundtruth_boxlists, groundtruth_classes_with_background_list,
            groundtruth_masks_list, groundtruth_weights_list)