def filter_boxes_keep_smaller(
    data: Mapping[str, list[Any]],
    iou_threshold: float = 0.8,
    area_threshold: int | None = None,
    min_area: int = 1000,
    margin: int = 5,
) -> dict[str, list[Any]]:
  """Filters overlapping bounding boxes, preferentially keeping smaller ones.

  This function sorts boxes by area and iterates through them, discarding any
  box that has a high IoU with an already-kept box or is contained within one.
  This is useful for eliminating duplicate or redundant detections.

  Args:
      data: A dictionary containing 'boxes' and 'masks' lists.
      iou_threshold: The IoU value above which a box is considered an overlap.
      area_threshold: An optional maximum area to consider for a box.
      min_area: The minimum area required for a box to be kept.
      margin: The pixel margin used for the containment check.

  Returns:
      A dictionary with the filtered 'boxes' and their corresponding 'masks'.
  """
  # Check if the input data is valid
  bounding_boxes = [_BoundingBox(*b) for b in data['boxes']]

  areas = ([_box_area(b) for b in bounding_boxes])

  # Sort boxes from smallest to largest area
  sorted_indices = np.argsort(areas)
  sorted_bounding_boxes = [bounding_boxes[i] for i in sorted_indices]

  masks = np.array(data['masks'])
  sorted_masks = masks[sorted_indices]

  kept_boxes = []
  kept_masks = []
  kept_bounding_boxes_for_check = []

  for i, box in enumerate(sorted_bounding_boxes):
    current_area = _box_area(box)
    if (
        area_threshold is not None and current_area > area_threshold
    ) or current_area < min_area:
      continue

    keep = True
    for kept_box in kept_bounding_boxes_for_check:
      if _calculate_iou(box, kept_box) > iou_threshold or _is_contained(
          kept_box, box, margin
      ):
        keep = False
        break

    if keep:
      kept_boxes.append([box.x1, box.y1, box.x2, box.y2])
      kept_masks.append(sorted_masks[i])
      kept_bounding_boxes_for_check.append(box)

  return {'boxes': kept_boxes, 'masks': kept_masks}