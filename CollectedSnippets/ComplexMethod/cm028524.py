def filter_masks(
    masks: np.ndarray,
    iou_threshold: float = 0.8,
    area_threshold: int | None = None,
) -> Sequence[int]:
  """Filter the overlapping masks.

  Filter the masks based on the area and intersection over union (IoU).

  Args:
    masks: The masks to filter.
    iou_threshold: The threshold for the intersection over union (IoU) between
      two masks.
    area_threshold: The threshold for the area of the mask.

  Returns:
    The indices of the unique masks.
  """
  # Calculate the area for each mask
  areas = np.array([_calculate_area(mask) for mask in masks])

  # Sort the masks based on area in descending order
  sorted_indices = np.argsort(areas)[::-1]
  sorted_masks = masks[sorted_indices]
  sorted_areas = areas[sorted_indices]

  unique_indices = []

  for i, mask in enumerate(sorted_masks):
    if (
        area_threshold is not None and sorted_areas[i] > area_threshold
    ) or sorted_areas[i] < 4000:
      continue

    keep = True
    for j in range(i):
      if _calculate_iou(mask, sorted_masks[j]) > iou_threshold or _is_contained(
          mask, sorted_masks[j]
      ):
        keep = False
        break
    if keep:
      unique_indices.append(sorted_indices[i])

  return unique_indices