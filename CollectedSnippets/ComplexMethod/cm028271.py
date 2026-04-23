def filter_annotations(img_all_annotations, used_classes):
  """Filters out annotations from the unused classes and dontcare regions.

  Filters out the annotations that belong to classes we do now wish to use and
  (optionally) also removes all boxes that overlap with dontcare regions.

  Args:
    img_all_annotations: A list of annotation dictionaries. See documentation of
      read_annotation_file for more details about the format of the annotations.
    used_classes: A list of strings listing the classes we want to keep, if the
    list contains "dontcare", all bounding boxes with overlapping with dont
    care regions will also be filtered out.

  Returns:
    img_filtered_annotations: A list of annotation dictionaries that have passed
      the filtering.
  """

  img_filtered_annotations = {}

  # Filter the type of the objects.
  relevant_annotation_indices = [
      i for i, x in enumerate(img_all_annotations['type']) if x in used_classes
  ]

  for key in img_all_annotations.keys():
    img_filtered_annotations[key] = (
        img_all_annotations[key][relevant_annotation_indices])

  if 'dontcare' in used_classes:
    dont_care_indices = [i for i,
                         x in enumerate(img_filtered_annotations['type'])
                         if x == 'dontcare']

    # bounding box format [y_min, x_min, y_max, x_max]
    all_boxes = np.stack([img_filtered_annotations['2d_bbox_top'],
                          img_filtered_annotations['2d_bbox_left'],
                          img_filtered_annotations['2d_bbox_bottom'],
                          img_filtered_annotations['2d_bbox_right']],
                         axis=1)

    ious = iou(boxes1=all_boxes,
               boxes2=all_boxes[dont_care_indices])

    # Remove all bounding boxes that overlap with a dontcare region.
    if ious.size > 0:
      boxes_to_remove = np.amax(ious, axis=1) > 0.0
      for key in img_all_annotations.keys():
        img_filtered_annotations[key] = (
            img_filtered_annotations[key][np.logical_not(boxes_to_remove)])

  return img_filtered_annotations