def add_single_ground_truth_image_info(self,
                                         image_id,
                                         groundtruth_dict):
    """Adds groundtruth for a single image to be used for evaluation.

    If the image has already been added, a warning is logged, and groundtruth is
    ignored.

    Args:
      image_id: A unique string/integer identifier for the image.
      groundtruth_dict: A dictionary containing -
        InputDataFields.groundtruth_boxes: float32 numpy array of shape
          [num_boxes, 4] containing `num_boxes` groundtruth boxes of the format
          [ymin, xmin, ymax, xmax] in absolute image coordinates.
        InputDataFields.groundtruth_classes: integer numpy array of shape
          [num_boxes] containing 1-indexed groundtruth classes for the boxes.
        InputDataFields.groundtruth_instance_masks: uint8 numpy array of shape
          [num_masks, image_height, image_width] containing groundtruth masks.
          The elements of the array must be in {0, 1}.
        InputDataFields.groundtruth_verified_neg_classes: [num_classes + 1]
          float indicator vector with values in {0, 1}. The length is
          num_classes + 1 so as to be compatible with the 1-indexed groundtruth
          classes.
        InputDataFields.groundtruth_not_exhaustive_classes: [num_classes + 1]
          float indicator vector with values in {0, 1}. The length is
          num_classes + 1 so as to be compatible with the 1-indexed groundtruth
          classes.
        InputDataFields.groundtruth_area (optional): float numpy array of
          shape [num_boxes] containing the area (in the original absolute
          coordinates) of the annotated object.
    Raises:
      ValueError: if groundtruth_dict is missing a required field
    """
    if image_id in self._image_id_to_mask_shape_map:
      tf.logging.warning('Ignoring ground truth with image id %s since it was '
                         'previously added', image_id)
      return
    for key in [fields.InputDataFields.groundtruth_boxes,
                fields.InputDataFields.groundtruth_classes,
                fields.InputDataFields.groundtruth_instance_masks,
                fields.InputDataFields.groundtruth_verified_neg_classes,
                fields.InputDataFields.groundtruth_not_exhaustive_classes]:
      if key not in groundtruth_dict.keys():
        raise ValueError('groundtruth_dict missing entry: {}'.format(key))

    groundtruth_instance_masks = groundtruth_dict[
        fields.InputDataFields.groundtruth_instance_masks]
    groundtruth_instance_masks = convert_masks_to_binary(
        groundtruth_instance_masks)
    verified_neg_classes_shape = groundtruth_dict[
        fields.InputDataFields.groundtruth_verified_neg_classes].shape
    not_exhaustive_classes_shape = groundtruth_dict[
        fields.InputDataFields.groundtruth_not_exhaustive_classes].shape
    if verified_neg_classes_shape != (len(self._category_id_set) + 1,):
      raise ValueError('Invalid shape for verified_neg_classes_shape.')
    if not_exhaustive_classes_shape != (len(self._category_id_set) + 1,):
      raise ValueError('Invalid shape for not_exhaustive_classes_shape.')
    self._image_id_to_verified_neg_classes[image_id] = np.flatnonzero(
        groundtruth_dict[
            fields.InputDataFields.groundtruth_verified_neg_classes]
        == 1).tolist()
    self._image_id_to_not_exhaustive_classes[image_id] = np.flatnonzero(
        groundtruth_dict[
            fields.InputDataFields.groundtruth_not_exhaustive_classes]
        == 1).tolist()

    # Drop optional fields if empty tensor.
    groundtruth_area = groundtruth_dict.get(
        fields.InputDataFields.groundtruth_area)
    if groundtruth_area is not None and not groundtruth_area.shape[0]:
      groundtruth_area = None

    self._groundtruth_list.extend(
        lvis_tools.ExportSingleImageGroundtruthToLVIS(
            image_id=image_id,
            next_annotation_id=self._annotation_id,
            category_id_set=self._category_id_set,
            groundtruth_boxes=groundtruth_dict[
                fields.InputDataFields.groundtruth_boxes],
            groundtruth_classes=groundtruth_dict[
                fields.InputDataFields.groundtruth_classes],
            groundtruth_masks=groundtruth_instance_masks,
            groundtruth_area=groundtruth_area)
    )

    self._annotation_id += groundtruth_dict[fields.InputDataFields.
                                            groundtruth_boxes].shape[0]
    self._image_id_to_mask_shape_map[image_id] = groundtruth_dict[
        fields.InputDataFields.groundtruth_instance_masks].shape