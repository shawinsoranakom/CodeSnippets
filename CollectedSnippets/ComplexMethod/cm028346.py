def add_single_ground_truth_image_info(self, image_id, groundtruth_dict):
    """Adds groundtruth for a single image to be used for evaluation.

    Args:
      image_id: A unique string/integer identifier for the image.
      groundtruth_dict: A dictionary containing -
        standard_fields.InputDataFields.groundtruth_boxes: float32 numpy array
          of shape [num_boxes, 4] containing `num_boxes` groundtruth boxes of
          the format [ymin, xmin, ymax, xmax] in absolute image coordinates.
        standard_fields.InputDataFields.groundtruth_classes: integer numpy array
          of shape [num_boxes] containing 1-indexed groundtruth classes for the
          boxes.
        standard_fields.InputDataFields.groundtruth_difficult: Optional length M
          numpy boolean array denoting whether a ground truth box is a difficult
          instance or not. This field is optional to support the case that no
          boxes are difficult.
        standard_fields.InputDataFields.groundtruth_instance_masks: Optional
          numpy array of shape [num_boxes, height, width] with values in {0, 1}.

    Raises:
      ValueError: On adding groundtruth for an image more than once. Will also
        raise error if instance masks are not in groundtruth dictionary.
    """
    if image_id in self._image_ids:
      logging.warning('Image with id %s already added.', image_id)

    groundtruth_classes = (
        groundtruth_dict[standard_fields.InputDataFields.groundtruth_classes] -
        self._label_id_offset)
    # If the key is not present in the groundtruth_dict or the array is empty
    # (unless there are no annotations for the groundtruth on this image)
    # use values from the dictionary or insert None otherwise.
    if (standard_fields.InputDataFields.groundtruth_difficult
        in six.viewkeys(groundtruth_dict) and
        (groundtruth_dict[standard_fields.InputDataFields.groundtruth_difficult]
         .size or not groundtruth_classes.size)):
      groundtruth_difficult = groundtruth_dict[
          standard_fields.InputDataFields.groundtruth_difficult]
    else:
      groundtruth_difficult = None
      if not len(self._image_ids) % 1000:
        logging.warning(
            'image %s does not have groundtruth difficult flag specified',
            image_id)
    groundtruth_masks = None
    if self._evaluate_masks:
      if (standard_fields.InputDataFields.groundtruth_instance_masks
          not in groundtruth_dict):
        raise ValueError('Instance masks not in groundtruth dictionary.')
      groundtruth_masks = groundtruth_dict[
          standard_fields.InputDataFields.groundtruth_instance_masks]
    self._evaluation.add_single_ground_truth_image_info(
        image_key=image_id,
        groundtruth_boxes=groundtruth_dict[
            standard_fields.InputDataFields.groundtruth_boxes],
        groundtruth_class_labels=groundtruth_classes,
        groundtruth_is_difficult_list=groundtruth_difficult,
        groundtruth_masks=groundtruth_masks)
    self._image_ids.update([image_id])