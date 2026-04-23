def filter_bounding_boxes(
    bounding_boxes: List[Tuple[int, int, int, int]],
    iou_threshold: float = 0.5,
    area_ratio_threshold: float = 0.8,
) -> Tuple[List[Tuple[int, int, int, int]], List[int]]:
  """Filters overlapping bounding boxes based on IoU and area ratio criteria.

  This function filters out overlapping bounding boxes from a given list based
  on Intersection over Union (IoU) and area ratio of the intersection to the
  smaller bounding box's area.

  Args:
      bounding_boxes: A list of bounding boxes, where each bounding box is
        represented as a tuple of (xmin, ymin, xmax, ymax).
      iou_threshold: Threshold for Intersection over Union. Bounding boxes with
        IoU above this threshold will be considered overlapping. Defaults to
        0.5.
      area_ratio_threshold: Threshold for the area ratio of the intersection to
        the smaller bounding box's area. Defaults to 0.8.

  Returns:
      tuple: A tuple containing:
          - filtered_boxes: A list of bounding boxes that passed the filtering
          criteria.
          - eliminated_indices: Indices of the bounding boxes that didn't pass
          the filtering criteria.

  Example:
      >>> bounding_boxes = [(10, 10, 50, 50), (20, 20, 60, 60)]
      >>> filter_bounding_boxes(bounding_boxes)
      ([(10, 10, 50, 50)], [1])
  """
  filtered_boxes = []
  eliminated_indices = []

  # Enumerate and sort the boxes based on their area in descending order
  enumerated_boxes = list(enumerate(bounding_boxes))
  sorted_boxes = sorted(
      enumerated_boxes,
      key=lambda item: (item[1][2] - item[1][0]) * (item[1][3] - item[1][1]),
      reverse=True,
  )

  for idx, bbox in sorted_boxes:
    skip_box = False

    # Calculate areas of individual bounding boxes
    area_bbox = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

    for jdx, other_bbox in sorted_boxes:
      if idx == jdx:
        continue

      # Calculate intersection coordinates
      xmin_inter = max(bbox[0], other_bbox[0])
      ymin_inter = max(bbox[1], other_bbox[1])
      xmax_inter = min(bbox[2], other_bbox[2])
      ymax_inter = min(bbox[3], other_bbox[3])

      # Calculate intersection area
      width_inter = max(0, xmax_inter - xmin_inter)
      height_inter = max(0, ymax_inter - ymin_inter)
      area_inter = width_inter * height_inter

      area_other_bbox = (other_bbox[2] - other_bbox[0]) * (
          other_bbox[3] - other_bbox[1]
      )

      # Calculate area ratio
      area_ratio = area_inter / min(area_bbox, area_other_bbox)

      # Check for overlapping and area ratio thresholds
      if area_ratio > area_ratio_threshold:
        if area_bbox > area_other_bbox:
          skip_box = True
          eliminated_indices.append(idx)
          break
      elif (
          area_inter > 0
          and area_inter / (area_bbox + area_other_bbox - area_inter)
          > iou_threshold
      ):
        if area_bbox > area_other_bbox:
          skip_box = True
          eliminated_indices.append(idx)
          break

    if not skip_box:
      filtered_boxes.append(bbox)

  return filtered_boxes, eliminated_indices