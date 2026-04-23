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
        InputDataFields.groundtruth_is_crowd (optional): integer numpy array of
          shape [num_boxes] containing iscrowd flag for groundtruth boxes.
        InputDataFields.groundtruth_area (optional): float numpy array of
          shape [num_boxes] containing the area (in the original absolute
          coordinates) of the annotated object.
        InputDataFields.groundtruth_keypoints (optional): float numpy array of
          keypoints with shape [num_boxes, num_keypoints, 2].
        InputDataFields.groundtruth_keypoint_visibilities (optional): integer
          numpy array of keypoint visibilities with shape [num_gt_boxes,
          num_keypoints]. Integer is treated as an enum with 0=not labeled,
          1=labeled but not visible and 2=labeled and visible.
        InputDataFields.groundtruth_labeled_classes (optional): a tensor of
          shape [num_classes + 1] containing the multi-hot tensor indicating the
          classes that each image is labeled for. Note that the classes labels
          are 1-indexed.
    """
    if image_id in self._image_ids:
      tf.logging.warning('Ignoring ground truth with image id %s since it was '
                         'previously added', image_id)
      return

    # Drop optional fields if empty tensor.
    groundtruth_is_crowd = groundtruth_dict.get(
        standard_fields.InputDataFields.groundtruth_is_crowd)
    groundtruth_area = groundtruth_dict.get(
        standard_fields.InputDataFields.groundtruth_area)
    groundtruth_keypoints = groundtruth_dict.get(
        standard_fields.InputDataFields.groundtruth_keypoints)
    groundtruth_keypoint_visibilities = groundtruth_dict.get(
        standard_fields.InputDataFields.groundtruth_keypoint_visibilities)
    if groundtruth_is_crowd is not None and not groundtruth_is_crowd.shape[0]:
      groundtruth_is_crowd = None
    if groundtruth_area is not None and not groundtruth_area.shape[0]:
      groundtruth_area = None
    if groundtruth_keypoints is not None and not groundtruth_keypoints.shape[0]:
      groundtruth_keypoints = None
    if groundtruth_keypoint_visibilities is not None and not groundtruth_keypoint_visibilities.shape[
        0]:
      groundtruth_keypoint_visibilities = None

    self._groundtruth_list.extend(
        coco_tools.ExportSingleImageGroundtruthToCoco(
            image_id=image_id,
            next_annotation_id=self._annotation_id,
            category_id_set=self._category_id_set,
            groundtruth_boxes=groundtruth_dict[
                standard_fields.InputDataFields.groundtruth_boxes],
            groundtruth_classes=groundtruth_dict[
                standard_fields.InputDataFields.groundtruth_classes],
            groundtruth_is_crowd=groundtruth_is_crowd,
            groundtruth_area=groundtruth_area,
            groundtruth_keypoints=groundtruth_keypoints,
            groundtruth_keypoint_visibilities=groundtruth_keypoint_visibilities)
    )

    self._annotation_id += groundtruth_dict[standard_fields.InputDataFields.
                                            groundtruth_boxes].shape[0]
    if (standard_fields.InputDataFields.groundtruth_labeled_classes
       ) in groundtruth_dict:
      labeled_classes = groundtruth_dict[
          standard_fields.InputDataFields.groundtruth_labeled_classes]
      if labeled_classes.shape != (len(self._category_id_set) + 1,):
        raise ValueError('Invalid shape for groundtruth labeled classes: {}, '
                         'num_categories_including_background: {}'.format(
                             labeled_classes,
                             len(self._category_id_set) + 1))
      self._groundtruth_labeled_classes[image_id] = np.flatnonzero(
          groundtruth_dict[standard_fields.InputDataFields
                           .groundtruth_labeled_classes] == 1).tolist()

    # Boolean to indicate whether a detection has been added for this image.
    self._image_ids[image_id] = False