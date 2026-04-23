def ExportSingleImageGroundtruthToLVIS(image_id,
                                       next_annotation_id,
                                       category_id_set,
                                       groundtruth_boxes,
                                       groundtruth_classes,
                                       groundtruth_masks=None,
                                       groundtruth_area=None):
  """Export groundtruth of a single image to LVIS format.

  This function converts groundtruth detection annotations represented as numpy
  arrays to dictionaries that can be ingested by the LVIS evaluation API. Note
  that the image_ids provided here must match the ones given to
  ExportSingleImageDetectionMasksToLVIS. We assume that boxes, classes and masks
  are in correspondence - that is, e.g., groundtruth_boxes[i, :], and
  groundtruth_classes[i] are associated with the same groundtruth annotation.

  In the exported result, "area" fields are always set to the area of the
  groundtruth bounding box.

  Args:
    image_id: a unique image identifier castable to integer.
    next_annotation_id: integer specifying the first id to use for the
      groundtruth annotations. All annotations are assigned a continuous integer
      id starting from this value.
    category_id_set: A set of valid class ids. Groundtruth with classes not in
      category_id_set are dropped.
    groundtruth_boxes: numpy array (float32) with shape [num_gt_boxes, 4]
    groundtruth_classes: numpy array (int) with shape [num_gt_boxes]
    groundtruth_masks: optional uint8 numpy array of shape [num_detections,
      image_height, image_width] containing detection_masks.
    groundtruth_area: numpy array (float32) with shape [num_gt_boxes]. If
      provided, then the area values (in the original absolute coordinates) will
      be populated instead of calculated from bounding box coordinates.

  Returns:
    a list of groundtruth annotations for a single image in the COCO format.

  Raises:
    ValueError: if (1) groundtruth_boxes and groundtruth_classes do not have the
      right lengths or (2) if each of the elements inside these lists do not
      have the correct shapes or (3) if image_ids are not integers
  """

  if len(groundtruth_classes.shape) != 1:
    raise ValueError('groundtruth_classes is '
                     'expected to be of rank 1.')
  if len(groundtruth_boxes.shape) != 2:
    raise ValueError('groundtruth_boxes is expected to be of '
                     'rank 2.')
  if groundtruth_boxes.shape[1] != 4:
    raise ValueError('groundtruth_boxes should have '
                     'shape[1] == 4.')
  num_boxes = groundtruth_classes.shape[0]
  if num_boxes != groundtruth_boxes.shape[0]:
    raise ValueError('Corresponding entries in groundtruth_classes, '
                     'and groundtruth_boxes should have '
                     'compatible shapes (i.e., agree on the 0th dimension).'
                     'Classes shape: %d. Boxes shape: %d. Image ID: %s' % (
                         groundtruth_classes.shape[0],
                         groundtruth_boxes.shape[0], image_id))

  groundtruth_list = []
  for i in range(num_boxes):
    if groundtruth_classes[i] in category_id_set:
      if groundtruth_area is not None and groundtruth_area[i] > 0:
        area = float(groundtruth_area[i])
      else:
        area = float((groundtruth_boxes[i, 2] - groundtruth_boxes[i, 0]) *
                     (groundtruth_boxes[i, 3] - groundtruth_boxes[i, 1]))
      export_dict = {
          'id':
              next_annotation_id + i,
          'image_id':
              int(image_id),
          'category_id':
              int(groundtruth_classes[i]),
          'bbox':
              list(_ConvertBoxToCOCOFormat(groundtruth_boxes[i, :])),
          'area': area,
      }
      if groundtruth_masks is not None:
        export_dict['segmentation'] = RleCompress(groundtruth_masks[i])

      groundtruth_list.append(export_dict)
  return groundtruth_list